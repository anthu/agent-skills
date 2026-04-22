---
name: audit-skill
description: "Audit skills against best practices. Use when: reviewing skills, checking quality, improving skills. Triggers: audit skill, review skill, improve skill."
---

# Audit Existing Skill

Review skill against best practices and provide improvements.

## Workflow

### Step 1: Load Skill

Ask for skill path or name. Search `.claude/skills/` if name provided.

Parse: frontmatter, sections, workflow steps, tools.

### Step 2: Audit Checklist

**Frontmatter:**
| Check | Severity |
|-------|----------|
| `name` present, kebab-case | 🔴 |
| `description` with triggers | 🔴 |
| Purpose explained | 🟡 |

**Structure:**
| Check | Severity |
|-------|----------|
| < 500 lines | 🟡 |
| Workflow section | 🔴 |
| Stopping points | 🔴 |
| Output section | 🟡 |

**Workflow:**
| Check | Severity |
|-------|----------|
| Numbered steps | 🟡 |
| ⚠️ checkpoints marked | 🔴 |
| No chaining without approval | 🔴 |
| Error handling guidance | 🟡 |
| Clear actions | 🟡 |

**Testing:**
| Check | Severity |
|-------|----------|
| Test prompts exist (`evals/evals.json`) | 🟡 |
| Happy path + edge case covered | 🟡 |
| Skill triggers correctly on test prompts | 🟡 |

**Tools (if applicable):**
| Check | Severity |
|-------|----------|
| All tools documented | 🟡 |
| Usage examples | 🟡 |
| Absolute paths for scripts | 🟡 |

### Step 3: Generate Report

```
# Audit Report: <skill-name>

## Summary
| Category | 🔴 | 🟡 | 🟢 |
|----------|---|---|---|
| Frontmatter | X | X | X |
| Structure | X | X | X |
| Workflow | X | X | X |

## Critical 🔴
1. [Issue] → [Fix]

## Warnings 🟡
1. [Issue] → [Fix]

## Suggestions 🟢
1. [Improvement]
```

**⚠️ STOP**: Present report.

### Step 4: Apply Fixes (Optional)

Ask:
```
1. Fix critical only
2. Fix critical + warnings
3. Fix all
4. Skip
```

For each fix: show change → approve → apply.

## Severity Guide

- 🔴 **Critical**: Skill may not work
- 🟡 **Warning**: Quality issue
- 🟢 **Suggestion**: Enhancement

## Stopping Points

- ✋ Step 1: Confirm skill loaded
- ✋ Step 3: Present report
- ✋ Step 4: Approve each fix

## Output

Audit report with categorized findings and optional fixes.
