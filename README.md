# Skills Repository

A collection of [skills](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-skills) primarily focused on Snowflake workflows, designed for use with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) but equally compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and similar AI coding assistants.

## Available Skills

| Skill | Description |
|-------|-------------|
| [dcm](dcm-projects/SKILL.md) | Database Change Management (DCM) for Snowflake infrastructure-as-code. Creates, modifies, and deploys DCM projects with full workflow support. |
| [openflow-layout](openflow-layout/SKILL.md) | Autonomously lays out NiFi/Openflow flows on the canvas using a Row-Grid algorithm. Organizes, tidies, and arranges processors and connections for clean visual flows. |
| [skills-sync](skills-sync/SKILL.md) | Publishes skills to a Snowflake instance so they can be [shared across your team](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-skills#sharing-skills). |

### DCM Sub-Skills

The `dcm` skill includes specialized sub-skills for different workflows:

- **create-project** — Create new DCM projects from scratch
- **modify-project** — Modify existing projects (with or without local source)
- **deploy-project** — Safe deployment with confirmation workflow
- **dcm-roles-and-grants** — Best practices for roles and grants in DCM
- **multi-project** — Hierarchical multi-project architectures
- **bulk-import** — Bulk schema discovery and import

## Prerequisites

- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), or a compatible AI coding assistant
- Active Snowflake connection (for Snowflake-specific skills)

## Local Setup

```bash
cortex skill add <path-to-this-repo>
```

## Team Access

Use the `skills-sync` skill to publish to Snowflake, then teammates can add them:

```bash
cortex skill add @CORTEX.SKILLS.SKILLS_STAGE/
```
