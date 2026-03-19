# Skills Repository

Personal Cortex Code skills, synced to Snowflake.

## Available Skills

| Skill | Description |
|-------|-------------|
| [dcm](dcm_projects/SKILL.md) | Database Change Management (DCM) for Snowflake infrastructure-as-code. Creates, modifies, and deploys DCM projects with full workflow support. |
| [skills-sync](skills-sync/SKILL.md) | Syncs local skills to Snowflake stage for team sharing. |

### DCM Sub-Skills

The `dcm` skill includes specialized sub-skills for different workflows:

- **create-project** — Create new DCM projects from scratch
- **modify-project** — Modify existing projects (with or without local source)
- **deploy-project** — Safe deployment with confirmation workflow
- **dcm-roles-and-grants** — Best practices for roles and grants
- **multi-project** — Hierarchical multi-project architectures
- **bulk-import** — Bulk schema discovery and import

## Prerequisites

- Cortex Code CLI
- Active Snowflake connection

## Local Setup

```bash
cortex skill add <path-to-this-repo>
```

## Sync to Snowflake

```bash
$skills-sync
```

## Team Access

After syncing, teammates can add skills from Snowflake:

```bash
cortex skill add @CORTEX.SKILLS.SKILLS_STAGE/
```
