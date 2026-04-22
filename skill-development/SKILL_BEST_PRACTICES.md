# Skill Best Practices

Proven patterns for creating effective skills. Read this before writing or auditing any skill.

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Skill Anatomy](#skill-anatomy)
3. [Writing Effective Descriptions](#writing-effective-descriptions)
4. [Designing Workflows](#designing-workflows)
5. [Writing Style](#writing-style)
6. [Scripts and Tools](#scripts-and-tools)
7. [Modularity and Sub-Skills](#modularity-and-sub-skills)
8. [Testing and Iteration](#testing-and-iteration)
9. [Strong Skill Domains](#strong-skill-domains)
10. [Common Pitfalls](#common-pitfalls)
11. [Quick Reference Checklist](#quick-reference-checklist)

---

## Core Principles

### Conciseness

The context window is shared — skills compete with conversation history, other skills, and user requests. Challenge every piece of information: "Does the agent really need this to do its job?"

- Keep SKILL.md under **500 lines**
- Move detailed reference material to `references/` files loaded on-demand
- The agent is already capable — only add what it doesn't already know

### Progressive Disclosure

Skills use a three-level loading system. Understanding this helps you put information in the right place:

1. **Metadata** (name + description) — Always in context (~100 words). This is how the agent decides whether to load your skill at all.
2. **SKILL.md body** — Loaded when the skill triggers. Keep it focused (<500 lines).
3. **Bundled resources** — Loaded on-demand. References, scripts, assets. No size limit; scripts can execute without being loaded into context.

### Degrees of Freedom

Match the level of specificity to how fragile the operation is:

| Freedom | When to Use | Format |
|---------|-------------|--------|
| **High** | Multiple valid approaches, context-dependent | Text instructions, heuristics |
| **Medium** | Preferred pattern exists, some variation OK | Pseudocode, parameterized examples |
| **Low** | Fragile operations, exact sequence required | Exact scripts, specific commands |

Think of it as a path: a narrow bridge needs guardrails (low freedom), while an open field allows many routes (high freedom).

### Explain Why, Not Just What

Instead of heavy-handed directives, explain *why* something matters. An agent that understands the reasoning behind a rule applies it more reliably than one given a bare imperative.

```markdown
# Less effective
ALWAYS validate the schema before deploying. NEVER skip this step.

# More effective
Validate the schema before deploying — a malformed schema silently drops
columns, and the error only surfaces when downstream queries fail hours later.
```

---

## Skill Anatomy

### Directory Structure

```
skill-name/
├── SKILL.md              # Required — entry point
├── pyproject.toml        # If skill has Python scripts
├── scripts/              # Executable code for deterministic tasks
├── references/           # Docs loaded into context as needed
├── assets/               # Files used in output (templates, icons)
└── sub-skill/            # Sub-skills for distinct workflow branches
    └── SKILL.md
```

### Required Sections in SKILL.md

```markdown
---
name: skill-name
description: "Clear description with trigger phrases"
---

# Skill Title

## Workflow
[Step-by-step instructions]

## Stopping Points
[Where to pause for user input]

## Output
[What the skill produces]
```

### Optional Sections

- **Prerequisites** — What needs to be in place before starting
- **Setup** — Load references, verify environment
- **Tools** — Script documentation with usage examples
- **Success Criteria** — How to verify completion
- **Troubleshooting** — Common issues and solutions

---

## Writing Effective Descriptions

The description is the **primary trigger mechanism** — it determines when the agent loads your skill. Getting it right is critical because agents tend to *undertrigger*: they'll skip a skill that could help unless the description clearly signals relevance.

### Make Descriptions Assertive

Be explicit about when the skill should fire. A little assertiveness prevents the agent from trying to handle the task manually when the skill exists for exactly that purpose.

```yaml
# Weak — agent will often skip this
description: "A skill for working with data quality metrics."

# Strong — agent knows when to trigger
description: "Monitor and assess data quality using Snowflake Data Metric
Functions. Use for ALL requests involving: data quality scores, DMF results,
schema health, quality trends, table comparison, or dataset popularity.
DO NOT attempt data quality work manually — invoke this skill first."
```

### Description Anatomy

A good description includes three parts:
1. **What it does** — purpose in one sentence
2. **When to use it** — specific scenarios and contexts
3. **Trigger keywords** — phrases that should activate it

```yaml
description: "Create, edit, and audit Cortex Code skills. Use when: creating
new skills, capturing session work as reusable workflows, reviewing skill
quality. Triggers: create skill, build skill, new skill, summarize session,
capture workflow, audit skill, review skill."
```

---

## Designing Workflows

### Step Structure

Use numbered steps with clear goals and actions:

```markdown
### Step 1: Gather Requirements

**Goal:** Understand what the user needs before writing anything.

1. **Ask** the user for skill name, purpose, and trigger scenarios
2. **Validate** inputs are complete

**Output:** Confirmed requirements

**⚠️ STOP**: Confirm requirements before proceeding.
```

### Mandatory Stopping Points

Mark where the workflow must pause for user input. This prevents the agent from chaining destructive or irreversible actions without approval.

```markdown
**⚠️ MANDATORY STOPPING POINT**: Present findings to user.
Do NOT proceed until user responds with approval.
```

Place stopping points:
- Before any destructive or irreversible action
- After analysis/diagnosis, before applying fixes
- At decision points where user preference matters
- Before final output delivery

### Decision Points

When the workflow branches, use a clear routing table:

```markdown
| Intent | Condition | Action |
|--------|-----------|--------|
| CREATE | User wants a new skill | **Load** `create/SKILL.md` |
| AUDIT  | User has an existing skill | **Load** `audit/SKILL.md` |
| TEST   | User wants to evaluate | **Load** `test/SKILL.md` |
```

### Error Handling

Tell the agent what to do when things go wrong:

```markdown
**If the command fails:**
- Permission error → Ask user to verify access
- Not found → Check the path and retry
- Unknown error → Present the error to the user and ask for guidance
```

---

## Writing Style

### Use Theory of Mind

Write skills that are general and not hyper-specific to one example. The agent should understand the *principle* behind the instructions so it can adapt to variations.

```markdown
# Too narrow
Run `snow sql -q "SELECT * FROM MY_TABLE"` to check the data.

# General principle
Query the target table to verify the data loaded correctly.
Use the appropriate tool for the user's environment (SQL execution tool,
CLI, or notebook).
```

### Draft, Then Revise

Start with a complete draft, then review it with fresh eyes:
- Is anything redundant with what the agent already knows?
- Are the stopping points in the right places?
- Would someone unfamiliar with the domain understand the workflow?
- Can any section be replaced with a pointer to a reference file?

### Accessibility

Skills may be used by people across a range of technical familiarity. Pay attention to context cues. When in doubt, briefly define jargon the first time you use it.

---

## Scripts and Tools

### When to Use Scripts

**Use scripts when:**
- The operation involves API calls or external services
- Logic is complex enough to benefit from a real programming language
- The same operation runs repeatedly with different parameters
- You need proper error handling, retries, or validation

**Keep it in markdown when:**
- Simple SQL queries (use the SQL execution tool)
- File operations the agent can do directly
- Straightforward logic that doesn't need abstraction

### Running Scripts with uv

Use `uv run` so dependencies install automatically from `pyproject.toml`:

```bash
# Always use absolute paths for both --project and the script
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/my_script.py [args]
```

Common mistakes:
```bash
# Wrong: relative script path
uv run --project /path/to/skill python scripts/my_script.py

# Wrong: cd then run
cd /path/to/skill && uv run python scripts/my_script.py

# Correct: absolute paths throughout
uv run --project /path/to/skill python /path/to/skill/scripts/my_script.py
```

### Script Documentation Pattern

```markdown
### Script: analyze.py

**Description**: Analyzes target resource state.

**Usage:**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/analyze.py \
  --target TARGET_NAME --output results.json
```

**Arguments:**
- `--target`: Resource identifier (required)
- `--output`: Output file path (default: stdout)

**When to use:** Before making changes, to understand current state.
```

### Script Best Practices

1. Use argparse for CLI arguments — makes scripts self-documenting
2. Handle errors gracefully with clear messages
3. Use environment variables for secrets — never hardcode credentials
4. Keep scripts focused — one script, one job
5. Never print secrets to console
6. Pass file paths for complex data (certificates, tokens) rather than reading content into context

### pyproject.toml

Every skill with scripts needs one:

```toml
[project]
name = "my-skill"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.32.0",
]
```

---

## Modularity and Sub-Skills

### When to Stay Simple

Keep everything in one SKILL.md when:
- The workflow is linear (no major branches)
- Total content is under ~500 lines
- The task has a single clear purpose

Many effective skills are just one file. Don't split prematurely.

### When to Split

Consider splitting when:
- Content exceeds ~500 lines
- 3+ distinct branches each with 3+ steps
- Different user intents require completely different workflows

### Two Approaches

**References** — For documentation/context loaded on-demand:
```
my-skill/
├── SKILL.md
└── references/
    ├── aws.md        # Loaded when user chooses AWS
    └── gcp.md        # Loaded when user chooses GCP
```

**Sub-Skills** — For distinct workflow branches:
```
my-skill/
├── SKILL.md          # Intent detection + routing
├── create/SKILL.md   # Full workflow for CREATE
└── debug/SKILL.md    # Full workflow for DEBUG
```

### CYOA Analysis for Modular Skills

Modular skills form a soft state machine — a directed graph where files/sections connect via routing decisions. Validate these properties:

| Property | Good | Bad |
|----------|------|-----|
| **Reachability** | Every file is loadable from the router | Orphaned files no route leads to |
| **Determinism** | Each decision point has defined outcomes | Ambiguous routing for some intents |
| **Termination** | Clear halting states (success, user choice, error) | Paths that trail off without direction |
| **Transition clarity** | Active voice: "Load X", "Continue to Y" | Passive: "return to...", "see also..." |
| **Loop bounds** | Retry logic has max attempts | Infinite loops with no escape |

Prefer directive transition language:
```markdown
# Good
**Load** `references/setup-auth.md` to configure authentication.

# Bad
Return to the setup workflow when done.
```

---

## Testing and Iteration

Skills benefit enormously from testing. The create-evaluate-iterate loop is how good skills become great.

### The Iteration Loop

```
Write draft skill
       ↓
Create 2-3 realistic test prompts
       ↓
Run the agent with the skill on each prompt
       ↓
Evaluate results (qualitative + quantitative)
       ↓
Identify gaps → Revise skill → Repeat
```

### Writing Test Prompts

Create prompts that represent what a real user would actually say — not sanitized lab conditions. Include:

- **Happy path** — the most common use case
- **Edge case** — unusual input or missing information
- **Ambiguous request** — forces the skill to interpret intent

Example for a data-quality skill:
```json
{
  "skill_name": "data-quality",
  "evals": [
    {
      "id": 1,
      "prompt": "Check if my customer table has good data quality",
      "expected_output": "DMF assessment with quality scores and recommendations"
    },
    {
      "id": 2,
      "prompt": "Compare PROD.CUSTOMERS with STAGING.CUSTOMERS",
      "expected_output": "Table diff showing row count, schema, and value differences"
    },
    {
      "id": 3,
      "prompt": "Is my data fresh?",
      "expected_output": "Freshness check — agent should ask which table"
    }
  ]
}
```

### What to Look For

When evaluating results, check:

- Did the skill trigger when it should have?
- Did the agent follow the workflow steps in order?
- Did it stop at the right checkpoints?
- Was the output format correct?
- Did it handle errors gracefully?
- Did it avoid doing things the skill didn't ask for?

### With-Skill vs Without-Skill

For objective tasks, run the same prompt with and without the skill. The delta tells you whether the skill is actually adding value or just adding latency.

### Improving the Description

After testing, revisit the description. If the skill didn't trigger on a prompt where it should have, add the missing keywords. If it triggered when it shouldn't have, narrow the conditions.

---

## Strong Skill Domains

Cortex Code has native tooling and deep integration for these domains — skills built here get the most leverage:

### Snowflake & Cortex
- **SQL execution**: Direct query execution with parsing, retry, and connection pooling
- **Cortex Analyst**: Semantic model validation, natural language to SQL
- **Semantic views**: Creation, debugging, optimization with YAML schema checking
- **Object discovery**: Semantic search for tables, views, schemas
- **Artifact management**: Create notebooks and files in Snowflake workspaces

### dbt & Data Engineering
- **dbt workflows**: Model creation, testing, documentation, lineage (`fdbt` provides fast native parsing)
- **Data validation**: Data diff tool for comparing query results
- **Pipeline orchestration**: ETL/ELT patterns, schema migrations, data quality

### SQL & Data Modeling
- **Complex SQL**: Stored procedures, dollar-delimited blocks, nested queries
- **Schema design**: Dimensional modeling, normalization patterns
- **Dynamic SQL**: Parameterized queries, templated transformations

---

## Common Pitfalls

### 1. Vague Descriptions

```yaml
# Agent won't know when to trigger
description: "A skill for doing things with data"

# Agent triggers reliably
description: "Use for ALL data quality tasks: DMF assessment, table comparison,
freshness checks, quality trends. Triggers: data quality, schema health,
compare tables, is my data fresh."
```

### 2. Missing Stopping Points

```markdown
# Agent chains actions without approval
### Step 3: Apply Changes
Apply all the changes identified above.

# Agent pauses for confirmation
### Step 3: Apply Changes
**⚠️ STOP**: Present planned changes. Wait for explicit approval before applying.
```

### 3. Unclear Tool Usage

```markdown
# Agent guesses at syntax
Run the script to process the data.

# Agent knows exactly what to do
```bash
uv run --project /path/to/skill python /path/to/skill/scripts/process.py \
  --input data.json --output result.json
```

### 4. No Error Handling

```markdown
# Agent is stuck when something fails
Step 3: Execute the command.

# Agent knows how to recover
Step 3: Execute the command.
**If error:** Permission denied → verify access. Not found → check path. Unknown → ask user.
```

### 5. Fabricated Commands

Never include commands you haven't verified. Plausible but nonexistent commands waste time and erode trust.

```markdown
# Bad — untested command
Generate a token: `snow session token --format JSON`

# Good — honest fallback
If no token is available, ask the user how they authenticate.
```

### 6. Unverified Assertions

Use flexible language when uncertain. Products evolve; stating "you must use X" becomes wrong when new options appear.

```markdown
# Brittle
On BYOC deployments, you must use key-pair authentication.

# Resilient
Key-pair is a common BYOC authentication method. Other options may be available.
```

### 7. Duplicated Content

Information should live in one place. Copies drift when the source changes.

```markdown
# Creates maintenance burden
See `other-skill` for details. Quick reference: [copy of other-skill content]

# Single source of truth
See `other-skill` for details.
```

---

## Quick Reference Checklist

When creating or auditing a skill, verify:

**Description:**
- [ ] Includes what it does + when to use + trigger keywords
- [ ] Assertive enough to prevent undertriggering
- [ ] Doesn't conflict with existing skill names

**Structure:**
- [ ] SKILL.md under 500 lines
- [ ] Only essential information (agent already knows general programming)
- [ ] Detailed content in `references/` if needed

**Workflow:**
- [ ] Steps are numbered with clear goals
- [ ] Stopping points before destructive/irreversible actions
- [ ] No chaining without user approval
- [ ] Error handling guidance at failure-prone steps

**Scripts (if applicable):**
- [ ] Documented with usage examples and arguments
- [ ] `pyproject.toml` for dependency management
- [ ] Absolute paths for `uv run`

**Testing:**
- [ ] 2-3 realistic test prompts created
- [ ] Results evaluated for triggering, workflow adherence, output quality
- [ ] Description refined based on trigger accuracy
