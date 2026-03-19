---
name: skills-sync
description: Syncs local skills to Snowflake stage for team sharing. Use when user says "sync skills", "publish skills", "push to snowflake", or wants to share skills with team.
---

# Skills Sync Workflow

## Steps

1. **Verify skills registered**
   ```bash
   cortex skill list
   ```

2. **Create Snowflake objects** (first time only)
   ```sql
   CREATE DATABASE IF NOT EXISTS CORTEX;
   CREATE SCHEMA IF NOT EXISTS CORTEX.SKILLS;
   CREATE STAGE IF NOT EXISTS CORTEX.SKILLS.SKILLS_STAGE DIRECTORY = (ENABLE = TRUE);
   ```

3. **Publish from current directory**
   ```bash
   cortex skill publish . --to-stage @CORTEX.SKILLS.SKILLS_STAGE/
   ```

4. **Verify**
   ```sql
   LIST @CORTEX.SKILLS.SKILLS_STAGE;
   ```
