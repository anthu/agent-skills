# Multi-Project DCM Patterns Reference

This reference provides templates and patterns for hierarchical DCM project architectures.

## Pattern 1: Platform + Team Projects

The most common pattern where a platform team provides infrastructure and teams build on top.

### Platform Project Template

**manifest.yml:**

```yaml
manifest_version: 2
type: DCM_PROJECT
default_target: 'DEV'

targets:
  DEV:
    account_identifier: MY_ACCOUNT
    project_name: 'ADMIN_DB.INFRASTRUCTURE.PLATFORM_DEV'
    project_owner: PLATFORM_ADMIN
    templating_config: 'DEV'
  PROD:
    account_identifier: MY_ACCOUNT
    project_name: 'ADMIN_DB.INFRASTRUCTURE.PLATFORM'
    project_owner: PLATFORM_ADMIN
    templating_config: 'PROD'

templating:
  defaults:
    env_suffix: '_DEV'
    shared_wh_size: 'SMALL'
    teams:
      - name: 'dev_team'
        wh_size: 'XSMALL'
        schema_prefix: 'DEV'
  configurations:
    DEV:
      env_suffix: '_DEV'
      shared_wh_size: 'XSMALL'
    PROD:
      env_suffix: ''
      shared_wh_size: 'LARGE'
      teams:
        - name: 'marketing'
          wh_size: 'MEDIUM'
          schema_prefix: 'MKT'
        - name: 'finance'
          wh_size: 'LARGE'
          schema_prefix: 'FIN'
        - name: 'analytics'
          wh_size: 'XLARGE'
          schema_prefix: 'ANL'
```

**sources/definitions/infrastructure.sql:**

```sql
-- Main data warehouse database
DEFINE DATABASE DATA_WAREHOUSE{{env_suffix}};

-- Team schemas
{% for team in teams %}
DEFINE SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_RAW;
DEFINE SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_ANALYTICS;
DEFINE SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_SERVE;
{% endfor %}

-- Shared warehouse
DEFINE WAREHOUSE SHARED_WH{{env_suffix}}
WITH
    WAREHOUSE_SIZE = '{{shared_wh_size}}'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE;

-- Team-specific warehouses
{% for team in teams %}
DEFINE WAREHOUSE {{team.name | upper}}_WH{{env_suffix}}
WITH
    WAREHOUSE_SIZE = '{{team.wh_size}}'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE;
{% endfor %}
```

**sources/definitions/access.sql:**

```sql
-- Platform admin role
DEFINE ROLE PLATFORM_ADMIN{{env_suffix}};

-- Team admin roles
{% for team in teams %}
DEFINE ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
{% endfor %}

-- Grant platform admin full access
GRANT USAGE ON DATABASE DATA_WAREHOUSE{{env_suffix}} TO ROLE PLATFORM_ADMIN{{env_suffix}};
GRANT CREATE SCHEMA ON DATABASE DATA_WAREHOUSE{{env_suffix}} TO ROLE PLATFORM_ADMIN{{env_suffix}};

-- Grant teams their warehouses
{% for team in teams %}
GRANT USAGE ON WAREHOUSE {{team.name | upper}}_WH{{env_suffix}} 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
GRANT USAGE ON WAREHOUSE SHARED_WH{{env_suffix}} 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
{% endfor %}

-- Grant teams ability to create DCM projects
{% for team in teams %}
GRANT CREATE DCM PROJECT ON SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_RAW 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
GRANT CREATE DCM PROJECT ON SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_ANALYTICS 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
{% endfor %}

-- Grant teams full control of their schemas
{% for team in teams %}
GRANT ALL ON SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_RAW 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
GRANT ALL ON SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_ANALYTICS 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
GRANT ALL ON SCHEMA DATA_WAREHOUSE{{env_suffix}}.{{team.schema_prefix}}_SERVE 
    TO ROLE {{team.name | upper}}_TEAM_ADMIN{{env_suffix}};
{% endfor %}
```

### Team Project Template

**manifest.yml:**

```yaml
manifest_version: 2
type: DCM_PROJECT
default_target: 'DEV'

targets:
  DEV:
    account_identifier: MY_ACCOUNT
    project_name: 'DATA_WAREHOUSE_DEV.MKT_RAW.MARKETING_PIPELINE'
    project_owner: MARKETING_TEAM_ADMIN_DEV
    templating_config: 'DEV'
  PROD:
    account_identifier: MY_ACCOUNT
    project_name: 'DATA_WAREHOUSE.MKT_RAW.MARKETING_PIPELINE'
    project_owner: MARKETING_TEAM_ADMIN
    templating_config: 'PROD'

templating:
  defaults:
    db: 'DATA_WAREHOUSE'
    schema_prefix: 'MKT'
    team_wh: 'MARKETING_WH'
    env_suffix: '_DEV'
  configurations:
    DEV:
      db: 'DATA_WAREHOUSE_DEV'
      team_wh: 'MARKETING_WH_DEV'
      env_suffix: '_DEV'
    PROD:
      db: 'DATA_WAREHOUSE'
      team_wh: 'MARKETING_WH'
      env_suffix: ''
```

**sources/definitions/tables.sql:**

```sql
-- Raw data tables
DEFINE TABLE {{db}}.{{schema_prefix}}_RAW.CAMPAIGNS (
    CAMPAIGN_ID NUMBER AUTOINCREMENT,
    CAMPAIGN_NAME VARCHAR(255),
    START_DATE DATE,
    END_DATE DATE,
    BUDGET NUMBER(15,2),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) CHANGE_TRACKING = TRUE;

DEFINE TABLE {{db}}.{{schema_prefix}}_RAW.CAMPAIGN_METRICS (
    METRIC_ID NUMBER AUTOINCREMENT,
    CAMPAIGN_ID NUMBER,
    METRIC_DATE DATE,
    IMPRESSIONS NUMBER,
    CLICKS NUMBER,
    CONVERSIONS NUMBER,
    SPEND NUMBER(15,2)
) CHANGE_TRACKING = TRUE;
```

**sources/definitions/analytics.sql:**

```sql
-- Dynamic tables for analytics
DEFINE DYNAMIC TABLE {{db}}.{{schema_prefix}}_ANALYTICS.CAMPAIGN_PERFORMANCE
    TARGET_LAG = '1 hour'
    WAREHOUSE = {{team_wh}}
AS
SELECT 
    c.CAMPAIGN_ID,
    c.CAMPAIGN_NAME,
    SUM(m.IMPRESSIONS) AS TOTAL_IMPRESSIONS,
    SUM(m.CLICKS) AS TOTAL_CLICKS,
    SUM(m.CONVERSIONS) AS TOTAL_CONVERSIONS,
    SUM(m.SPEND) AS TOTAL_SPEND,
    CASE WHEN SUM(m.CLICKS) > 0 
         THEN SUM(m.CONVERSIONS) / SUM(m.CLICKS) * 100 
         ELSE 0 END AS CONVERSION_RATE
FROM {{db}}.{{schema_prefix}}_RAW.CAMPAIGNS c
JOIN {{db}}.{{schema_prefix}}_RAW.CAMPAIGN_METRICS m ON c.CAMPAIGN_ID = m.CAMPAIGN_ID
GROUP BY c.CAMPAIGN_ID, c.CAMPAIGN_NAME;
```

---

## Pattern 2: Data Mesh (Domain-Oriented)

Each business domain owns its data as a product.

### Structure

```
SALES_DOMAIN/
├── SALES_DOMAIN.CORE.SALES_PROJECT
│   ├── Raw sales data
│   ├── Sales transformations
│   └── Sales data products (views for consumers)

MARKETING_DOMAIN/
├── MARKETING_DOMAIN.CORE.MARKETING_PROJECT
│   ├── Raw marketing data
│   ├── Marketing transformations
│   └── Marketing data products

SHARED_DOMAIN/
├── SHARED_DOMAIN.CORE.MASTER_DATA_PROJECT
│   ├── Customer master
│   ├── Product master
│   └── Reference data
```

### Cross-Domain Access Pattern

Domains can read from other domains' data products but cannot modify them:

```sql
-- In Marketing domain project
DEFINE VIEW MARKETING_DOMAIN.SERVE.CUSTOMER_CAMPAIGNS AS
SELECT 
    c.CUSTOMER_ID,
    c.CUSTOMER_NAME,
    m.CAMPAIGN_ID,
    m.SPEND
FROM SHARED_DOMAIN.SERVE.CUSTOMER_MASTER c  -- Read from shared domain
JOIN MARKETING_DOMAIN.ANALYTICS.CAMPAIGN_METRICS m ON c.CUSTOMER_ID = m.CUSTOMER_ID;
```

---

## Pattern 3: Environment Separation

Completely separate accounts or databases per environment.

### Same Account, Different Databases

```yaml
targets:
  DEV:
    account_identifier: MY_ACCOUNT
    project_name: 'DEV_DB.PROJECTS.MY_PROJECT'
    project_owner: DEV_DEPLOYER
    templating_config: 'DEV'
  STAGING:
    account_identifier: MY_ACCOUNT
    project_name: 'STAGING_DB.PROJECTS.MY_PROJECT'
    project_owner: STAGING_DEPLOYER
    templating_config: 'STAGING'
  PROD:
    account_identifier: MY_ACCOUNT
    project_name: 'PROD_DB.PROJECTS.MY_PROJECT'
    project_owner: PROD_DEPLOYER
    templating_config: 'PROD'
```

### Different Accounts per Environment

```yaml
targets:
  DEV:
    account_identifier: MYORG_DEV
    project_name: 'DATA_WAREHOUSE.PROJECTS.MY_PROJECT'
    project_owner: DCM_DEPLOYER
    templating_config: 'DEV'
  PROD:
    account_identifier: MYORG_PROD
    project_name: 'DATA_WAREHOUSE.PROJECTS.MY_PROJECT'
    project_owner: DCM_DEPLOYER
    templating_config: 'PROD'
```

---

## Privilege Grant Patterns

### Granting DCM Project Creation

```sql
-- Grant ability to create DCM projects in a specific schema
GRANT CREATE DCM PROJECT ON SCHEMA <database>.<schema> TO ROLE <team_admin_role>;

-- Grant ability to create DCM projects in any schema of a database
GRANT CREATE DCM PROJECT ON DATABASE <database> TO ROLE <team_admin_role>;
```

### Three-Tier Role Pattern

```sql
-- Admin: Full control
DEFINE ROLE {{team}}_ADMIN;

-- Developer: Read/write data, create objects
DEFINE ROLE {{team}}_DEVELOPER;

-- Analyst: Read-only access
DEFINE ROLE {{team}}_ANALYST;

-- Hierarchy
GRANT ROLE {{team}}_ANALYST TO ROLE {{team}}_DEVELOPER;
GRANT ROLE {{team}}_DEVELOPER TO ROLE {{team}}_ADMIN;
```

---

## Batch Project Creation Script

For creating multiple team projects with consistent structure:

```bash
#!/bin/bash
# create_team_projects.sh

TEAMS=("marketing" "finance" "analytics" "sales")
CONNECTION="myconnection"
TEMPLATE_DIR="./team_project_template"
BASE_DIR="./projects"

for team in "${TEAMS[@]}"; do
    TEAM_UPPER=$(echo "$team" | tr '[:lower:]' '[:upper:]')
    PROJECT_DIR="${BASE_DIR}/${team}_project"
    
    echo "Creating project for ${team}..."
    
    # Copy template
    cp -r "$TEMPLATE_DIR" "$PROJECT_DIR"
    
    # Replace placeholders
    find "$PROJECT_DIR" -type f -name "*.yml" -o -name "*.sql" | while read file; do
        sed -i '' "s/{{TEAM_NAME}}/${team}/g" "$file"
        sed -i '' "s/{{TEAM_NAME_UPPER}}/${TEAM_UPPER}/g" "$file"
    done
    
    # Create DCM project in Snowflake
    snow dcm create "DATA_WAREHOUSE.${TEAM_UPPER}_RAW.${TEAM_UPPER}_PIPELINE" -c "$CONNECTION"
    
    echo "  Created: DATA_WAREHOUSE.${TEAM_UPPER}_RAW.${TEAM_UPPER}_PIPELINE"
done

echo "Done! Created ${#TEAMS[@]} projects."
```

---

## CI/CD Considerations

### Deployment Order

When using hierarchical projects, deploy in order:

1. **Platform project first** (creates containers and grants)
2. **Team projects after** (depend on platform infrastructure)

### GitHub Actions Example

```yaml
jobs:
  deploy-platform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy Platform
        run: |
          cd platform_project
          snow dcm plan ADMIN_DB.INFRA.PLATFORM -c ${{ secrets.SF_CONNECTION }} --save-output
          snow dcm deploy ADMIN_DB.INFRA.PLATFORM -c ${{ secrets.SF_CONNECTION }} --alias "${{ github.sha }}"

  deploy-teams:
    needs: deploy-platform
    runs-on: ubuntu-latest
    strategy:
      matrix:
        team: [marketing, finance, analytics]
    steps:
      - uses: actions/checkout@v4
      - name: Deploy ${{ matrix.team }}
        run: |
          cd ${{ matrix.team }}_project
          snow dcm deploy DATA_WAREHOUSE.${{ matrix.team }}_RAW.${{ matrix.team }}_PIPELINE \
            -c ${{ secrets.SF_CONNECTION }} --alias "${{ github.sha }}"
```
