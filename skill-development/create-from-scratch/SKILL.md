---
name: create-skill-from-scratch
description: "Create new skills from scratch. Use when user wants to build a new skill with proper structure."
---

# Create Skill from Scratch

## Workflow

### Step 1: Gather Requirements

Ask user:
```
To create your skill:
1. **Name** (kebab-case): e.g., "optimize-database"
2. **Purpose**: What problem does it solve?
3. **Triggers**: Words that should activate it
4. **Tools/Scripts**: Any scripts or APIs?
```

**⚠️ STOP**: Confirm requirements before proceeding.

### Step 2: Design Structure

Determine if single-file or needs splitting:
- **Single file**: Linear workflow, <500 lines
- **With references/**: Detailed docs needed on-demand
- **With sub-skills**: Distinct workflow branches

Present structure for approval.

**⚠️ STOP**: Get approval on structure.

### Step 3: Choose Location

Options:
1. `.claude/skills/<name>/`
2. `<repo>/skills/<name>/`
3. Custom path

Create directory: `mkdir -p <path>/<skill-name>`

### Step 4: Write SKILL.md

**Frontmatter:**
```yaml
---
name: skill-name
description: "Purpose. Use when: [scenarios]. Triggers: keyword1, keyword2."
---
```

**Body:**
```markdown
# Title

## Workflow
### Step 1: [Name]
[Actions]
**⚠️ STOP**: [Checkpoint]

## Stopping Points
- ✋ After Step X

## Output
[What skill produces]
```

### Step 5: Add Tools (if needed)

```markdown
## Tools
### script.py
**Usage:** `uv run --project <DIR> python <DIR>/scripts/script.py [args]`
```

### Step 6: Write and Present

1. Write SKILL.md
2. Verify < 500 lines
3. Present result with triggers

**⚠️ STOP**: Final review.

### Step 7: Create Test Prompts (Recommended)

After the skill is written, create 2-3 realistic test prompts — the kind of thing a real user would say. Share them with the user for confirmation.

Save test cases to `evals/evals.json` in the skill directory:
```json
{
  "skill_name": "my-skill",
  "evals": [
    {"id": 1, "prompt": "Happy path prompt", "expected_output": "Description"},
    {"id": 2, "prompt": "Edge case prompt", "expected_output": "Description"},
    {"id": 3, "prompt": "Ambiguous prompt", "expected_output": "Description"}
  ]
}
```

Run the agent with the skill on each prompt and evaluate:
- Did the skill trigger correctly?
- Did the agent follow workflow steps in order?
- Did it stop at the right checkpoints?

Refine the skill description and workflow based on results.

## Stopping Points

- ✋ Step 1: Requirements confirmed
- ✋ Step 2: Structure approved
- ✋ Step 6: Final review
- ✋ Step 7: Test prompts confirmed

## Output

Complete SKILL.md at specified location, optionally with test cases in `evals/evals.json`.
