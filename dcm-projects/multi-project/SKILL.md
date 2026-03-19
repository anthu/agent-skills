---
name: multi-project
description: "Hierarchical and multi-project DCM patterns. Triggers: multiple dcm projects, team projects, platform admin, hierarchical dcm, delegate deployment, platform infrastructure"
---

# Multi-Project DCM Architecture

## Overview

This sub-skill guides you through setting up hierarchical DCM project structures where:
- A **platform admin** deploys foundational infrastructure (databases, warehouses, base roles)
- **Team admins** deploy their own DCM projects on top of the platform layer

This pattern enables delegated ownership while maintaining governance.

## When to Use

Use this workflow when:
- Multiple teams need their own DCM projects with separate deployment responsibilities
- A platform team provides shared infrastructure (databases, warehouses, integrations)
- You need to delegate `CREATE DCM PROJECT` privileges to team-level roles
- Projects need to reference objects defined in other projects

## Hierarchical Pattern Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  PLATFORM PROJECT (deployed by Platform Admin)                   │
│  ├── Databases & Schemas (containers for team projects)         │
│  ├── Warehouses (shared compute)                                │
│  ├── Base Roles (PLATFORM_ADMIN, TEAM_ADMIN)                    │
│  ├── Integrations (storage, API, notification)                  │
│  └── GRANT CREATE DCM PROJECT to TEAM_ADMIN roles               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TEAM PROJECTS (deployed by Team Admins)                         │
│  ├── Tables, Views, Dynamic Tables                              │
│  ├── Tasks for ETL                                              │
│  ├── Team-specific roles & grants                               │
│  └── Data quality expectations                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Workflow

### Step 1: Gather Requirements

**Ask the user:**

1. **How many levels of hierarchy?**
   - Two-tier (platform + teams) is most common
   - Three-tier (org → platform → team) for large organizations

2. **What does the platform provide?**
   - Databases and schemas (containers)
   - Warehouses (shared or per-team)
   - External integrations (storage integrations, API integrations)
   - Base roles and privilege model

3. **What do teams own?**
   - Tables, views, dynamic tables
   - Team-specific transformations
   - Fine-grained access control within their scope

4. **Who deploys what?**
   - Platform admin role for infrastructure
   - Team admin roles for team-level objects

### Step 2: Design the Platform Project

The platform project defines the foundation. Key objects:

```sql
-- Platform-level databases (containers for teams)
DEFINE DATABASE ANALYTICS;
DEFINE DATABASE DATA_WAREHOUSE;

-- Shared warehouses
DEFINE WAREHOUSE SHARED_WH WITH WAREHOUSE_SIZE = '{{platform_wh_size}}';

-- Per-team warehouses (optional)
{% for team in teams %}
DEFINE WAREHOUSE {{team.name | upper}}_WH WITH WAREHOUSE_SIZE = '{{team.wh_size}}';
{% endfor %}

-- Platform admin role
DEFINE ROLE PLATFORM_ADMIN;

-- Team admin roles
{% for team in teams %}
DEFINE ROLE {{team.name | upper}}_TEAM_ADMIN;
{% endfor %}

-- Grant teams ability to create DCM projects in their schema
{% for team in teams %}
GRANT CREATE DCM PROJECT ON SCHEMA ANALYTICS.{{team.name | upper}} 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN;
{% endfor %}
```

### Step 3: Design Team Projects

Each team project references platform objects but owns its internal structure:

```sql
-- Team tables (inside platform-provided schema)
DEFINE TABLE ANALYTICS.{{team_name}}.RAW_EVENTS (
    EVENT_ID NUMBER,
    EVENT_TYPE VARCHAR,
    CREATED_AT TIMESTAMP_NTZ
) CHANGE_TRACKING = TRUE;

-- Team dynamic tables
DEFINE DYNAMIC TABLE ANALYTICS.{{team_name}}.DAILY_SUMMARY
    TARGET_LAG = '1 hour'
    WAREHOUSE = {{team_name}}_WH
AS
SELECT DATE_TRUNC('day', CREATED_AT) AS EVENT_DATE,
       COUNT(*) AS EVENT_COUNT
FROM ANALYTICS.{{team_name}}.RAW_EVENTS
GROUP BY 1;

-- Team-specific roles (database roles scoped to their area)
DEFINE DATABASE ROLE ANALYTICS.{{team_name}}_READER;
DEFINE DATABASE ROLE ANALYTICS.{{team_name}}_WRITER;

-- Grants within team scope
GRANT SELECT ON ALL TABLES IN SCHEMA ANALYTICS.{{team_name}} 
    TO DATABASE ROLE ANALYTICS.{{team_name}}_READER;
```

### Step 4: Create Platform Project First

1. **Create the platform manifest.yml:**

```yaml
manifest_version: 2
type: DCM_PROJECT
default_target: 'DEV'

targets:
  DEV:
    account_identifier: MY_ACCOUNT
    project_name: 'ADMIN_DB.PROJECTS.PLATFORM_INFRA'
    project_owner: PLATFORM_ADMIN
    templating_config: 'DEV'
  PROD:
    account_identifier: MY_ACCOUNT
    project_name: 'ADMIN_DB.PROJECTS.PLATFORM_INFRA'
    project_owner: PLATFORM_ADMIN
    templating_config: 'PROD'

templating:
  defaults:
    platform_wh_size: 'SMALL'
    teams:
      - name: 'marketing'
        wh_size: 'SMALL'
      - name: 'finance'
        wh_size: 'MEDIUM'
      - name: 'analytics'
        wh_size: 'LARGE'
  configurations:
    DEV:
      platform_wh_size: 'XSMALL'
      teams:
        - name: 'dev_team'
          wh_size: 'XSMALL'
    PROD:
      platform_wh_size: 'LARGE'
      teams:
        - name: 'marketing'
          wh_size: 'MEDIUM'
        - name: 'finance'
          wh_size: 'LARGE'
        - name: 'analytics'
          wh_size: 'XLARGE'
```

2. **Deploy platform project:**

```bash
snow dcm create ADMIN_DB.PROJECTS.PLATFORM_INFRA -c <connection>
snow dcm plan ADMIN_DB.PROJECTS.PLATFORM_INFRA -c <connection> --save-output
# Review plan
snow dcm deploy ADMIN_DB.PROJECTS.PLATFORM_INFRA -c <connection> --alias "platform-v1"
```

### Step 5: Create Team Projects

After platform deployment, team admins can create their projects:

1. **Team manifest.yml:**

```yaml
manifest_version: 2
type: DCM_PROJECT
default_target: 'DEV'

targets:
  DEV:
    account_identifier: MY_ACCOUNT
    project_name: 'ANALYTICS.MARKETING.MARKETING_PIPELINE'
    project_owner: MARKETING_TEAM_ADMIN
    templating_config: 'DEV'
  PROD:
    account_identifier: MY_ACCOUNT
    project_name: 'ANALYTICS.MARKETING.MARKETING_PIPELINE'
    project_owner: MARKETING_TEAM_ADMIN
    templating_config: 'PROD'

templating:
  defaults:
    team_name: 'MARKETING'
    team_wh: 'MARKETING_WH'
  configurations:
    DEV:
      team_name: 'DEV_TEAM'
      team_wh: 'DEV_WH'
    PROD:
      team_name: 'MARKETING'
      team_wh: 'MARKETING_WH'
```

2. **Deploy team project:**

```bash
snow dcm create ANALYTICS.MARKETING.MARKETING_PIPELINE -c <connection>
snow dcm plan ANALYTICS.MARKETING.MARKETING_PIPELINE -c <connection> --save-output
snow dcm deploy ANALYTICS.MARKETING.MARKETING_PIPELINE -c <connection> --alias "marketing-v1"
```

## Key Constraints

### DCM Project Cannot Define Its Parent

A DCM project at `DATABASE.SCHEMA.PROJECT` **cannot** define that DATABASE or SCHEMA. The platform project must create containers first.

```
Platform project: ADMIN_DB.PROJECTS.PLATFORM
  → Defines: ANALYTICS database, ANALYTICS.MARKETING schema

Team project: ANALYTICS.MARKETING.PIPELINE  
  → Can define: tables, views inside ANALYTICS.MARKETING
  → Cannot define: ANALYTICS database or ANALYTICS.MARKETING schema
```

### Cross-Project References

Team projects can reference platform objects but don't "own" them:

```sql
-- Team project references platform warehouse (defined in platform project)
DEFINE DYNAMIC TABLE ANALYTICS.MARKETING.SUMMARY
    WAREHOUSE = MARKETING_WH  -- Created by platform project
    ...
```

### Privilege Delegation

The platform must explicitly grant `CREATE DCM PROJECT`:

```sql
GRANT CREATE DCM PROJECT ON SCHEMA ANALYTICS.MARKETING 
    TO ROLE MARKETING_TEAM_ADMIN;
```

## Batch Creation Pattern

To create multiple team projects with consistent structure, use a script:

```bash
#!/bin/bash
TEAMS=("marketing" "finance" "analytics")
CONNECTION="myconnection"

for team in "${TEAMS[@]}"; do
    echo "Creating DCM project for $team..."
    
    # Create project directory from template
    cp -r team_template "${team}_project"
    
    # Substitute team name in manifest
    sed -i '' "s/{{TEAM_NAME}}/${team}/g" "${team}_project/manifest.yml"
    sed -i '' "s/{{TEAM_NAME}}/${team}/g" "${team}_project/sources/definitions/"*.sql
    
    # Create and deploy
    snow dcm create "ANALYTICS.${team^^}.${team^^}_PIPELINE" -c "$CONNECTION"
    cd "${team}_project"
    snow dcm plan "ANALYTICS.${team^^}.${team^^}_PIPELINE" -c "$CONNECTION" --save-output
    # Review before deploy
    cd ..
done
```

## Common Patterns

### Pattern: Shared Services Project

A project that provides utility functions, common views, or shared reference data:

```
ADMIN_DB.SHARED.COMMON_SERVICES
  ├── Utility functions (date helpers, string formatters)
  ├── Reference tables (country codes, currency rates)
  └── Common views (unified customer view)
```

Teams reference these with `SELECT * FROM ADMIN_DB.SHARED.CUSTOMER_VIEW`.

### Pattern: Data Mesh

Each domain owns its data products:

```
SALES_DOMAIN.CORE.SALES_PROJECT
MARKETING_DOMAIN.CORE.MARKETING_PROJECT  
FINANCE_DOMAIN.CORE.FINANCE_PROJECT
```

Each domain project is fully independent with its own database.

### Pattern: Environment Isolation

Separate accounts for environments:

```yaml
targets:
  DEV:
    account_identifier: DEV_ACCOUNT
    project_name: 'ANALYTICS.PROJECTS.PIPELINE_DEV'
  PROD:
    account_identifier: PROD_ACCOUNT
    project_name: 'ANALYTICS.PROJECTS.PIPELINE'
```

## Next Steps

After setting up the multi-project architecture:

1. **Document the hierarchy** for team admins
2. **Create templates** for new team projects
3. **Set up CI/CD** with appropriate role contexts for each project
4. **Establish change management** processes between platform and team deployments
