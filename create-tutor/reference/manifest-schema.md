# workshop.yaml Schema Reference

The `workshop.yaml` file is a machine-generated checkpoint produced by the `$create-tutor` GENERATE mode. It persists the analysis results so EVOLVE mode can diff against it when the workshop content changes.

While primarily machine-generated, the author can edit it to refine hints, fix metadata, or add environment errors. The schema below documents all fields.

## Top-Level Structure

```yaml
workshop:
  name: "Workshop Name"
  slug: "workshop-slug"
  version: "1.0"
  duration: "3h"
  audience: "Target audience description"
  description: "One-sentence description of what participants build"

modules:
  - id: "module_id"
    title: "Module Title"
    notebook: "notebook_filename"
    duration: "35min"
    exercises: [...]

environment:
  errors: [...]

progress_tracking:
  enabled: true
  tag_prefix: "workshop_slug"
  modes: ["hol", "sol", "sql", "sql_sol"]
```

## Module Schema

```yaml
modules:
  - id: "explore_parse"
    title: "Explore & Parse Documents"
    notebook: "hol_01_explore_parse"
    duration: "35min"
    exercises:
      - id: 1
        cell_name: "exercise_cell_name"
        title: "Exercise Title"
        concept: "One-sentence concept description"
        type: "exercise"        # exercise | pre_built | capstone
        hints:
          L1: "Concept-level hint text"
          L2: "Structure-level hint with code skeleton"
          L3: "solution_ref"    # or full solution text
        solution_file: "solutions/solution_01.ipynb"
        solution_cell: "exercise_cell_name"
        tags: ["relevant", "keywords"]
        common_errors:
          - pattern: "Error message pattern"
            fix: "How to fix it"
```

## Exercise Types

| Type | Description | Tutor Behavior |
|------|-------------|---------------|
| `exercise` | Participant writes code (`YOUR CODE HERE`) | Coach with graduated hints |
| `pre_built` | DDL/code provided, participant just runs it | Fix errors directly |
| `capstone` | Open-ended exercise (e.g., Streamlit app) | Coach with high freedom |

## Hint Levels

| Level | Content | When Given |
|-------|---------|------------|
| `L1` | Concept explanation, no code | First ask |
| `L2` | Function signature / code skeleton | Second ask |
| `L3` | Full solution or `"solution_ref"` (read from solution file) | Third ask or explicit request |

When `L3` is `"solution_ref"`, the tutor reads the actual solution from the referenced solution file at runtime.

## Environment Errors

```yaml
environment:
  errors:
    - pattern: "Error message text or pattern"
      fix: "Direct fix instructions for the participant"
```

These are setup-related errors (wrong warehouse, missing permissions) — not exercise errors. The tutor gives these fixes directly without coaching.

## Progress Tracking

```yaml
progress_tracking:
  enabled: true
  tag_prefix: "workshop_slug"
  tag_format: '{"PREFIX_ex": N, "nb": "notebook_id", "mode": "MODE"}'
  modes:
    - "hol"      # HOL notebook exercises
    - "sol"      # Solution notebooks
    - "sql"      # SQL worksheet scripts
    - "sql_sol"  # Solution SQL scripts
```

When enabled, the generated tutor skill includes instructions to never remove or modify QUERY_TAG statements.
