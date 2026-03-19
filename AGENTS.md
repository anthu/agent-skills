# Skills Repository

Cortex Code skills managed via git, synced to Snowflake.

## Creating New Skills

1. Create directory: `my-skill/`
2. Add `SKILL.md` with YAML frontmatter (name, description required)
3. Test locally: `$my-skill`
4. Publish: `$skills-sync`

## Skill Structure

### Required: SKILL.md Frontmatter

```yaml
---
name: my-skill
description: "Does X for Y. Use when user wants to Z. Triggers: keyword1, keyword2."
---
```

**Description best practices:**
- Use third-person ("Creates...", "Syncs...", "Modifies...")
- Include "Use when..." for trigger context
- List trigger keywords at the end

### Optional: Sub-Skills

For complex skills, organize into sub-skills:

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

### Optional: Reference Materials

Place detailed reference docs in `reference/` folder. Parent skill loads these as needed.

### Optional: Helper Scripts

Place automation scripts in `scripts/` folder. Include usage examples in the skill documentation.

## Sync Workflow

- **Local → Snowflake:** `$skills-sync`
- **Local → Git:** `git commit && git push`

## Testing Before Publishing

1. Invoke skill locally: `$my-skill`
2. Test all documented workflows
3. Verify frontmatter description triggers correctly
4. Run `cortex skill list` to confirm registration
