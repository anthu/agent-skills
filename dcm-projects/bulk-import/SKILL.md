---
name: bulk-import
description: "Bulk import existing Snowflake objects into DCM. Triggers: import schema, bulk import, discover objects, scan database, migrate to dcm, cross-account migration, adopt existing, convert to dcm"
---

# Bulk Import Objects into DCM

## Overview

This sub-skill guides you through discovering and importing existing Snowflake objects into a DCM project. Use this when you need to:
- Import all objects from a schema or database into DCM
- Discover what objects exist before selective import
- Migrate objects from one account to another via DCM
- Convert manually-created infrastructure to DCM-managed

## When to Use

Use this workflow when:
- Importing **many objects** (>5) from existing schemas
- You need to **discover** what objects exist before deciding what to import
- Performing **cross-account migration** (export DDL from source, create DCM for target)
- Converting an **entire schema** to DCM management

For importing 1-5 specific objects, the simpler workflow in [../modify-project/SKILL.md](../modify-project/SKILL.md) may be sufficient.

## Step-by-Step Workflow

### Step 1: Gather Import Requirements

**Ask the user:**

1. **Source scope**: What database/schema to import from?
2. **Object types**: All objects or specific types (tables, views, dynamic tables)?
3. **Target DCM project**: Existing project or create new?
4. **Cross-account?**: Same account or migrating to different account?

### Step 2: Run Discovery

Use the discovery script to scan the source schema:

```bash
python <skill-dir>/scripts/discover_schema.py \
    --connection <connection> \
    --database <source_db> \
    --schema <source_schema> \
    --output <output_directory>
```

Or run discovery queries manually:

```sql
-- Discover all tables
SHOW TABLES IN SCHEMA <database>.<schema>;

-- Discover all views
SHOW VIEWS IN SCHEMA <database>.<schema>;

-- Discover all dynamic tables
SHOW DYNAMIC TABLES IN SCHEMA <database>.<schema>;

-- Discover stages (check for external vs internal)
SHOW STAGES IN SCHEMA <database>.<schema>;

-- Discover tasks
SHOW TASKS IN SCHEMA <database>.<schema>;

-- Discover warehouses (if importing warehouses)
SHOW WAREHOUSES;

-- Discover roles with grants on this schema
SHOW GRANTS ON SCHEMA <database>.<schema>;
SHOW GRANTS ON DATABASE <database>;
```

### Step 3: Categorize Discovered Objects

**Before importing, categorize every object:**

| Category | Object Types | DCM Handling |
|----------|--------------|--------------|
| ✅ **DEFINE-able** | Tables, Views, Dynamic Tables, Warehouses, Internal Stages, Roles, Database Roles, Functions, Tasks | Convert `CREATE` → `DEFINE` |
| ⚠️ **POST_HOOK** | External Stages (with URL), Streams, Alerts, Pipes | Use `ATTACH POST_HOOK` |
| ❌ **Unsupported Grants** | `GRANT ... ON ACCOUNT`, `GRANT IMPORTED PRIVILEGES` | Document in `post_deployment_grants.sql` |

**How to identify external stages:**

```sql
DESC STAGE <database>.<schema>.<stage_name>;
-- If "url" field has a value (s3://, azure://, gcs://), it's external
```

**Present categorization to user:**

```
📊 Discovery Results for MY_DB.MY_SCHEMA:

✅ DEFINE-able (will convert to DCM):
   - 15 Tables
   - 8 Views
   - 3 Dynamic Tables
   - 2 Internal Stages
   - 1 Warehouse

⚠️  POST_HOOK required:
   - 2 External Stages (S3)
   - 1 Stream

❌ Unsupported (manual post-deployment):
   - 3 GRANT ... ON ACCOUNT statements

Proceed with import? (yes/no)
```

### Step 4: Extract DDL

**Bulk DDL extraction query:**

```sql
-- Generate DDL for all tables in schema
SELECT 
    'TABLE' AS object_type,
    table_name,
    GET_DDL('TABLE', table_catalog || '.' || table_schema || '.' || table_name) AS ddl
FROM information_schema.tables
WHERE table_schema = '<SCHEMA>'
  AND table_catalog = '<DATABASE>'
  AND table_type = 'BASE TABLE';

-- Generate DDL for all views
SELECT 
    'VIEW' AS object_type,
    table_name,
    GET_DDL('VIEW', table_catalog || '.' || table_schema || '.' || table_name) AS ddl
FROM information_schema.views
WHERE table_schema = '<SCHEMA>'
  AND table_catalog = '<DATABASE>';

-- Generate DDL for dynamic tables
SELECT 
    'DYNAMIC_TABLE' AS object_type,
    name,
    GET_DDL('DYNAMIC_TABLE', database_name || '.' || schema_name || '.' || name) AS ddl
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLES())
WHERE schema_name = '<SCHEMA>'
  AND database_name = '<DATABASE>';

-- Generate DDL for stages
SELECT 
    'STAGE' AS object_type,
    stage_name,
    GET_DDL('STAGE', stage_catalog || '.' || stage_schema || '.' || stage_name) AS ddl
FROM information_schema.stages
WHERE stage_schema = '<SCHEMA>'
  AND stage_catalog = '<DATABASE>';
```

### Step 5: Convert DDL to DEFINE Statements

**Conversion rules:**

1. **Replace `CREATE` with `DEFINE`** for supported objects
2. **Remove `OR REPLACE`** (DCM handles idempotency)
3. **Remove `IF NOT EXISTS`** (DCM handles existence checks)
4. **Keep all properties** exactly as they are
5. **Use fully qualified names** everywhere

**Example conversions:**

```sql
-- Original DDL
CREATE OR REPLACE TABLE MY_DB.MY_SCHEMA.CUSTOMERS (
    ID NUMBER AUTOINCREMENT,
    NAME VARCHAR(255),
    EMAIL VARCHAR(255)
);

-- Converted to DCM
DEFINE TABLE MY_DB.MY_SCHEMA.CUSTOMERS (
    ID NUMBER AUTOINCREMENT,
    NAME VARCHAR(255),
    EMAIL VARCHAR(255)
);
```

```sql
-- Original external stage
CREATE STAGE MY_DB.MY_SCHEMA.S3_STAGE
    URL = 's3://my-bucket/path/'
    STORAGE_INTEGRATION = MY_S3_INT;

-- Converted to POST_HOOK (external stages cannot use DEFINE)
ATTACH POST_HOOK AS [
    CREATE STAGE IF NOT EXISTS MY_DB.MY_SCHEMA.S3_STAGE
        URL = 's3://my-bucket/path/'
        STORAGE_INTEGRATION = MY_S3_INT;
];
```

### Step 6: Organize into Definition Files

Place converted definitions in appropriate files:

```
sources/definitions/
├── infrastructure.sql    # Databases, schemas, warehouses, internal stages
├── tables.sql           # All table definitions
├── views.sql            # All view definitions  
├── dynamic_tables.sql   # All dynamic table definitions
├── tasks.sql            # All task definitions
├── access.sql           # Roles and supported grants
├── hooks.sql            # ATTACH POST_HOOK for external stages, streams
└── post_deployment/
    └── unsupported_grants.sql  # Manual grants (ON ACCOUNT, etc.)
```

### Step 7: Validate Adoption

**Run analyze:**

```bash
snow dcm raw-analyze <project_identifier> -c <connection> --target <target>
```

Check output for errors.

**Run plan:**

```bash
snow dcm plan <project_identifier> -c <connection> --target <target> --save-output
```

**⚠️ CRITICAL: Verify zero changes for adopted objects**

Read `out/plan/plan_result.json` and verify:
- Adopted objects appear in the plan
- They show **NO operations** (not CREATE, not ALTER)

If plan shows CREATE or ALTER for an adopted object:
1. The definition doesn't exactly match the existing object
2. Compare DCM definition with actual DDL
3. Adjust definition until plan shows zero changes

### Step 8: Handle Cross-Account Migration

For migrating objects from Account A to Account B:

1. **Extract DDL from source account** (Account A):
   ```bash
   python discover_schema.py --connection source_conn --database DB --schema SCHEMA --output ./export
   ```

2. **Review and adjust for target account**:
   - Update database/schema names if different
   - Update integration names (storage integrations are account-specific)
   - Update role names if using different naming conventions
   - Remove account-specific references

3. **Create DCM project in target account** (Account B):
   ```bash
   snow dcm create TARGET_DB.SCHEMA.PROJECT -c target_conn
   ```

4. **Deploy to target**:
   - Plan will show CREATE for all objects (they don't exist yet)
   - This is expected for cross-account migration

## Discovery Script Reference

The `scripts/discover_schema.py` script automates discovery:

```bash
python discover_schema.py \
    --connection <snowflake_connection> \
    --database <database_name> \
    --schema <schema_name> \
    --output <output_directory> \
    [--include-grants] \
    [--object-types tables,views,dynamic_tables]
```

### Example Usage

```bash
# Full schema discovery
python <skill-dir>/scripts/discover_schema.py \
    --connection myconn \
    --database ANALYTICS \
    --schema RAW \
    --output ./dcm_import

# Discovery with specific object types
python <skill-dir>/scripts/discover_schema.py \
    -c myconn -d ANALYTICS -s RAW -o ./dcm_import \
    --object-types tables,views
```

### Script Help

```
usage: discover_schema.py [-h] --connection CONNECTION --database DATABASE
                          --schema SCHEMA --output OUTPUT [--include-grants]
                          [--object-types OBJECT_TYPES]

Discover Snowflake schema objects for DCM import

options:
  -h, --help            show this help message and exit
  --connection, -c      Snowflake connection name
  --database, -d        Database name
  --schema, -s          Schema name
  --output, -o          Output directory
  --include-grants      Include grant discovery
  --object-types        Comma-separated object types (default: all)
```

**Output structure:**

```
output_directory/
├── discovery_report.json     # Full inventory with categorization
├── definitions/
│   ├── tables.sql           # DEFINE TABLE statements
│   ├── views.sql            # DEFINE VIEW statements
│   ├── dynamic_tables.sql   # DEFINE DYNAMIC TABLE statements
│   ├── stages.sql           # DEFINE STAGE (internal only)
│   └── warehouses.sql       # DEFINE WAREHOUSE statements
├── hooks/
│   └── post_hooks.sql       # External stages, streams, etc.
└── unsupported/
    └── grants.sql           # Grants requiring manual application
```

## Selective Import

If you don't want to import everything:

1. **Run discovery** to see all objects
2. **Review `discovery_report.json`** with the user
3. **Ask user to select** which objects to import
4. **Generate definitions** only for selected objects

```
📋 Select objects to import:

Tables (15 found):
  [x] CUSTOMERS
  [x] ORDERS
  [ ] TEMP_STAGING  (skip - temporary table)
  [x] PRODUCTS

Views (8 found):
  [x] CUSTOMER_SUMMARY
  [ ] DEBUG_VIEW  (skip - development only)
  ...
```

## Common Issues

### Issue: Plan shows ALTER for adopted object

**Cause**: Definition doesn't exactly match existing object

**Solution**:
1. Run `SELECT GET_DDL('TABLE', 'DB.SCHEMA.TABLE')` for exact DDL
2. Compare with your DEFINE statement
3. Look for differences in:
   - Column order
   - Default values
   - Constraints
   - Properties (CHANGE_TRACKING, DATA_RETENTION, etc.)

### Issue: External stage in DEFINE

**Cause**: External stages (with URL) cannot use DEFINE

**Solution**: Move to `ATTACH POST_HOOK`:
```sql
ATTACH POST_HOOK AS [
    CREATE STAGE IF NOT EXISTS DB.SCHEMA.MY_EXTERNAL_STAGE
        URL = 's3://bucket/path'
        STORAGE_INTEGRATION = MY_INT;
];
```

### Issue: Grant errors during plan

**Cause**: Some grant patterns are unsupported

**Solution**: 
1. Load [../dcm-roles-and-grants/SKILL.md](../dcm-roles-and-grants/SKILL.md)
2. Categorize grants per that skill's guidance
3. Move unsupported grants to `post_deployment_grants.sql`

## Next Steps

After successful bulk import:

1. **Run `snow dcm deploy`** to register ownership
2. **Set up CI/CD** for ongoing changes
3. **Document** which objects are now DCM-managed
4. **Apply manual grants** from `post_deployment_grants.sql`
