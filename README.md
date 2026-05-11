# Skills Repository

A collection of [skills](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-skills) primarily focused on Snowflake workflows, designed for use with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) but equally compatible with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and similar AI coding assistants.

## Available Skills

| Skill | Description |
|-------|-------------|
| [create-tutor](create-tutor/SKILL.md) | Generates an AI tutor for any Cortex Code workshop. Agentically explores existing notebooks, SQL scripts, and solutions to produce a tutor skill with graduated hints, error triage, and solution validation. |
| [dcm-projects](dcm-projects/SKILL.md) | Database Change Management (DCM) for Snowflake infrastructure-as-code. Creates, modifies, and deploys DCM projects with full workflow support. |
| [event-sync](event-sync/SKILL.md) | Sync marketing events from a Google Sheet to an Apple/Google Calendar. Reads a sheet tab, filters by region, web-searches event details, and creates calendar entries with HTML-formatted descriptions. |
| [openflow-layout](openflow-layout/SKILL.md) | Autonomously lays out NiFi/Openflow flows on the canvas using a Row-Grid algorithm. Organizes, tidies, and arranges processors and connections for clean visual flows. |
| [skills-sync](skills-sync/SKILL.md) | Publishes skills to a Snowflake instance so they can be [shared across your team](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-skills#sharing-skills). |
| [streamlit-multipage-nav](streamlit-multipage-nav/SKILL.md) | Builds reliable multi-page Streamlit apps using st.navigation and st.Page. Covers directory structure, shared components, session state, and the critical pages/ vs views/ directory conflict. |
| [skill-development](skill-development/SKILL.md) | Create, test, and audit skills for Cortex Code. Includes best practices reference, eval-driven iteration workflow, and sub-skills for creating from scratch, summarizing sessions, and auditing existing skills. |
| [daily-note](daily-note/SKILL.md) | Create or update today's Obsidian daily note with meeting blocks from iCal. Fetches calendar events and generates a structured daily note with meeting sections. |
| [sync-projects](sync-projects/SKILL.md) | Generate Obsidian project documentation from AI conversation history. Scans Cortex Code and Claude Code conversations, groups by project, and generates rich Obsidian notes with summaries and timelines. |

### Create-Tutor Sub-Skills

The `create-tutor` skill includes specialized sub-skills:

- **analyze** — Agentically explores a workshop repo to discover exercises, solutions, and structure
- **generate** — Generates tutor SKILL.md, AGENTS.md, workshop.yaml, and graduated hints from analysis
- **evolve** — Updates tutor infrastructure after workshop content changes or author feedback

### DCM Sub-Skills

The `dcm-projects` skill includes specialized sub-skills for different workflows:

- **create-project** — Create new DCM projects from scratch
- **modify-project** — Modify existing projects (with or without local source)
- **deploy-project** — Safe deployment with confirmation workflow
- **dcm-roles-and-grants** — Best practices for roles and grants in DCM
- **multi-project** — Hierarchical multi-project architectures
- **bulk-import** — Bulk schema discovery and import

## Prerequisites

- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), or a compatible AI coding assistant
- Active Snowflake connection (for Snowflake-specific skills)

## Adding Skills

### Option 1: Add from Git (recommended)

Add all skills directly from this repository:

```bash
cortex skill add https://github.com/anthu/agent-skills.git
```

Or using the slash command inside a Cortex Code session:

```
/skill add https://github.com/anthu/agent-skills.git
```

Skills are cached locally. To update to the latest version:

```
/skill sync
```

### Option 2: Add from a local clone

Clone the repo and add by path:

```bash
git clone https://github.com/anthu/agent-skills.git
cortex skill add /path/to/agent-skills
```

### Option 3: Add from Snowflake (team access)

If a teammate has published skills to Snowflake using the `skills-sync` skill, add them from a stage:

```bash
cortex skill add @CORTEX.SKILLS.SKILLS_STAGE/
```

### Verify installation

List all loaded skills to confirm they were added:

```bash
cortex skill list
```

Or inside a session:

```
/skill list
```

You should see `create-tutor`, `daily-note`, `dcm-projects`, `event-sync`, `openflow-layout`, `skills-sync`, `streamlit-multipage-nav`, `skill-development`, and `sync-projects` in the output.

### Using a skill

Invoke a skill by name with the `$` prefix:

```
$dcm-projects Create a new project for my analytics database
$openflow-layout Organize the processors in my flow
```

## Creating New Skills

Each skill is a directory containing a `SKILL.md` file with YAML frontmatter and markdown instructions.

### 1. Create the skill directory

```bash
mkdir my-skill
```

### 2. Add `SKILL.md`

```markdown
---
name: my-skill
description: "Does X for Y. Use when user wants to Z. Triggers: keyword1, keyword2."
---

# My Skill

## When to Use

- Describe when this skill should be invoked

## Instructions

Step-by-step guidance for the AI when this skill is active.
```

**Frontmatter fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique identifier for the skill |
| `description` | Yes | Shown in skill listings; controls when the skill triggers |
| `tools` | No | List of tools to enable (e.g., `snowflake_sql_execute`) |

**Description best practices:**
- Use third-person ("Creates...", "Syncs...", "Modifies...")
- Include "Use when..." for trigger context
- List trigger keywords at the end

### 3. (Optional) Add sub-skills

For complex skills, organize into sub-skills with their own `SKILL.md`:

```
my-skill/
├── SKILL.md              # Parent skill with intent detection
├── sub-skill-a/
│   └── SKILL.md          # Loaded when intent matches
├── sub-skill-b/
│   └── SKILL.md
├── reference/            # Reference documentation
│   └── syntax.md
└── scripts/              # Helper scripts
    └── helper.py
```

### 4. Test locally

```
$my-skill Test it out
```

### 5. Publish

Commit and push to share via Git:

```bash
git add my-skill/
git commit -m "Add my-skill"
git push
```

To share via Snowflake, use the `skills-sync` skill:

```
$skills-sync
```
