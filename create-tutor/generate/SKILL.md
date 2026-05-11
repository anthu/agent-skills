---
name: generate
description: "Sub-skill for generating tutor infrastructure from analyzed workshop content."
---

# Generate Tutor Infrastructure

This sub-skill takes the approved analysis from the ANALYZE phase and generates all tutor infrastructure files.

## Prerequisites

- The ANALYZE sub-skill has been run and the author has approved the findings
- The tutor pedagogy reference (`reference/tutor-pedagogy.md`) is loaded
- The analysis results (exercises, modules, solutions, metadata) are in conversation context

## Workflow

### Step 1: Generate Hints

For each discovered exercise, generate L1/L2/L3 hints by reading the exercise instructions and solution code.

**For exercises WITH solutions:**

- **L1 (Concept)**: Summarize what the exercise teaches. Extract from the markdown instructions above the exercise cell. Focus on the function or pattern being introduced. No code in L1.
- **L2 (Structure)**: Read the solution code and extract the function signature or code skeleton. Replace specific values (table names, column names, file paths, literal strings) with generic placeholders. Show the shape of the answer.
- **L3 (Solution reference)**: Point to the solution file and cell name. Also include the complete solution SQL/code inline for quick reference.

**For exercises WITHOUT solutions:**

- **L1 (Concept)**: Same as above — extract from exercise instructions.
- **L2 (Structure)**: Best-effort extraction from the exercise instructions and any code examples in the surrounding markdown. If the instructions include a function signature or syntax example, use that.
- **L3**: Note: "Solution not provided. Add a solutions file for complete tutor coverage."

**Hint quality guidelines** (from tutor-pedagogy.md):
- L1 should be conceptual and reference what the participant sees in their code
- L2 should show the pattern without giving away the specific values
- L3 should be complete, correct, and never auto-executed

### Step 2: Generate workshop.yaml

Write `workshop.yaml` to the workshop root directory using the manifest schema from `reference/manifest-schema.md`.

Populate from the analysis:
- Workshop metadata (name, slug, description from README)
- Module structure (one per notebook/logical group)
- Exercise list with cell names, titles, concepts, hint text
- Environment errors (inferred from setup cells and common Snowflake patterns)
- Progress tracking config (if QUERY_TAG was detected in the analysis)

The slug should be derived from the workshop name: lowercase, hyphens, no special characters. The author can change it.

### Step 3: Generate tutor SKILL.md

**Load** `reference/tutor-template.md` and fill all `{{placeholder}}` values:

1. **`{{DESCRIPTION}}`**: Build an assertive description that includes:
   - What the tutor does
   - Exercise cell names as trigger keywords
   - Key concepts taught (Snowflake functions, SQL patterns, etc.)
   - "MUST also use when a 'fix the error' request targets any notebook cell"
   - "MUST also use when a participant asks to validate, check, or review their solution"

2. **`{{WORKSHOP_NAME}}`**: From analysis metadata

3. **`{{WORKSHOP_STRUCTURE_TABLE}}`**: Markdown table with notebook names, topics, and exercise ranges

4. **`{{EXERCISE_CELL_LIST}}`**: Comma-separated list of all exercise cell names for triage

5. **`{{PRE_BUILT_EXERCISE_NOTE}}`**: If any exercises are pre-built DDL (no YOUR CODE HERE), note them: "Exercises N-M have pre-built DDL — there is no YOUR CODE HERE. If participants hit errors on these cells, fix directly (no coaching needed)."

6. **`{{EXERCISE_IDENTIFICATION_LIST}}`**: Per-notebook exercise list with cell names and one-line concept descriptions

7. **`{{HINTS_BY_EXERCISE}}`**: The L1/L2/L3 hints generated in Step 1, formatted as:
   ```
   **Exercise N — [Title]**:
   - L1: "[concept hint]"
   - L2: `[code skeleton]`
   - L3: [full solution or reference]
   ```

8. **`{{SQL_FALLBACK_SECTION}}`**: If SQL scripts were found in the analysis, generate a fallback table mapping notebooks to SQL files

9. **`{{ENVIRONMENT_ERRORS}}`**: Common setup errors inferred from:
   - Warehouse references in setup cells
   - Database/schema references
   - External access integration references
   - Standard Snowflake workshop patterns (wrong warehouse, missing permissions, object not found)

10. **`{{PROGRESS_TRACKING_SECTION}}`**: If QUERY_TAG was detected, add instructions to never remove tracking tags

11. **`{{SOLUTIONS_PATH}}`**: Path to the solutions directory (e.g., `solutions/`). Used in the tutor template for referencing where to find solution files.

Write the generated tutor SKILL.md to `.snowflake/cortex/skills/tutor/SKILL.md` in the workshop directory (creating directories if needed).

### Step 4: Generate AGENTS.md

**Load** `reference/agents-template.md` and fill all `{{placeholder}}` values from the analysis and generated content.

If an `AGENTS.md` already exists in the workshop directory:
- Read it first
- Preserve any sections not related to the tutor (e.g., custom context, provisioning notes)
- Add/update the exercise reference, error fixing, and validation routing sections
- Ask the author before overwriting: "An AGENTS.md already exists. Shall I merge the tutor sections into it, or replace it entirely?"

Write the generated AGENTS.md to the workshop root directory.

### Step 5: Generate Progress Tracking Config

If QUERY_TAG patterns were detected in the analysis:
- Document the tag format in both the tutor SKILL.md and AGENTS.md
- Generate a dashboard query template that the author can use to monitor progress:

```sql
SELECT
    user_name,
    TRY_PARSE_JSON(query_tag):{{PREFIX}}_ex::INT AS exercise_id,
    TRY_PARSE_JSON(query_tag):nb::STRING AS notebook,
    TRY_PARSE_JSON(query_tag):mode::STRING AS mode,
    execution_status,
    start_time,
    total_elapsed_time
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
    END_TIME_RANGE_START => DATEADD('hours', -8, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 10000
))
WHERE query_tag LIKE '%{{PREFIX}}_ex%'
ORDER BY start_time DESC;
```

If no QUERY_TAG was detected, suggest adding it: "Consider instrumenting exercises with ALTER SESSION SET QUERY_TAG for real-time progress monitoring."

### Step 6: Present Generation Report

Summarize everything generated in a clear report:

```
Generation Report
=================

Files Generated:
  1. workshop.yaml — Workshop manifest (machine checkpoint)
  2. .snowflake/cortex/skills/tutor/SKILL.md — Tutor skill
  3. AGENTS.md — Workspace context [new/updated]

Tutor Configuration:
  Exercises covered: [N]
  Hint levels generated: L1/L2/L3 for [N] exercises
  Solution validation: [enabled/limited — N solutions found]
  Environment errors: [N] common patterns cataloged
  Progress tracking: [enabled/suggested]

--- AI-Generated Hints (review recommended) ---

Exercise 1: [title]
  L1: [hint text]
  L2: [hint text]
  L3: [solution reference or text]

Exercise 2: [title]
  L1: [hint text]
  L2: [hint text]
  L3: [solution reference or text]

[... all exercises ...]

These hints were AI-generated from your exercise instructions and solutions.
Please review them for accuracy and pedagogical quality.
```

**STOP**: Wait for the author to review all generated files and the hints. The author may ask to refine specific hints, add environment errors, or adjust the tutor configuration.

## Output

| File | Location | Purpose |
|------|----------|---------|
| `workshop.yaml` | Workshop root | Machine checkpoint for EVOLVE mode |
| `tutor/SKILL.md` | `.snowflake/cortex/skills/tutor/` | Participant-facing tutor skill |
| `AGENTS.md` | Workshop root | Cortex Code workspace context |

## Error Handling

- **Template not found**: If reference templates can't be loaded, report the error and generate inline (without template structure)
- **Existing files**: Always ask before overwriting existing AGENTS.md or tutor SKILL.md
- **Very large workshops** (>20 exercises): Warn the author that the tutor SKILL.md may exceed the recommended 500-line limit. Suggest splitting into sub-skills per module if this happens.
