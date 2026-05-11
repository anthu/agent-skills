---
name: analyze
description: "Sub-skill for analyzing a workshop repository to discover exercises, solutions, and structure."
---

# Analyze Workshop

This sub-skill agentically explores a workshop repository to discover its structure, exercises, solutions, and metadata. It uses Glob, Grep, and Read — no assumed folder conventions.

## Prerequisites

The tutor pedagogy reference (`reference/tutor-pedagogy.md`) should already be loaded by the parent skill.

## Workflow

### Phase 1: Broad Discovery

**Goal**: Understand the repository shape before diving into content.

Run these Glob patterns to discover what files exist:

1. `**/*.ipynb` — all Jupyter notebooks
2. `**/*.sql` — all SQL files
3. `**/solution*` or `**/solutions/**` — solution directories and files
4. `**/README*` — documentation
5. `**/AGENTS.md` — existing Cortex Code context
6. `**/WORKSHOP.md` or `**/INSTRUCTOR*` — instructor guides
7. `**/_build*` or `**/build_*` — build/generation scripts
8. `**/*.py` — Python files (build scripts, UDFs, Streamlit apps)
9. `**/*SKILL.md` — existing skills
10. `**/*.yaml` or `**/*.yml` — config files, semantic models

Present the discovered file tree to the user: "Here's what I found in your workshop. Let me explore the content."

### Phase 2: Content Detection

**Goal**: Find exercise markers and workshop patterns.

Run Grep searches across all discovered files:

1. **Exercise markers**: `-- YOUR CODE HERE` or `# YOUR CODE HERE` — the universal exercise placeholder
2. **Build script patterns**: `exercise(` or `def exercise` — programmatic exercise definitions
3. **Progress tracking**: `QUERY_TAG` or `query_tag` — instrumented progress tracking
4. **Key functions and patterns**: Search for technology-specific function calls that reveal what the workshop teaches. Common patterns to look for:
   - Snowflake AI: `AI_PARSE_DOCUMENT`, `AI_COMPLETE`, `AI_EXTRACT`, `AI_FILTER`, `AI_CLASSIFY`, `AI_SUMMARIZE`, `CORTEX`, `SEMANTIC VIEW`, `CORTEX SEARCH`, `CORTEX AGENT`
   - SQL patterns: `WINDOW`, `OVER`, `PARTITION BY`, `CTE`, `WITH`, `PIVOT`, `UNPIVOT`, `MERGE`, `LATERAL`
   - Python/ML: `import`, `def `, `class `, `snowflake.ml`, `snowpark`, `pandas`, `sklearn`
   - dbt: `ref(`, `source(`, `config(`
   - General: Look for any function names, import statements, or API calls that appear in exercise cells — these indicate the workshop's domain
5. **Solution indicators**: `solution` in filenames or directory names
6. **Cell metadata**: `"name":` in notebook JSON — named cells

Record which files contain exercise markers, which contain solutions, and which contain setup/infrastructure.

### Phase 3: Deep Read

**Goal**: Extract exercise details, instructions, and solution content.

For each file with exercise markers:

#### For Notebooks (.ipynb):
1. Read the notebook file (it's JSON)
2. For each cell containing `-- YOUR CODE HERE`:
   - Record the cell index and cell name (from `metadata.name` if present)
   - Read the markdown cell immediately ABOVE it — this contains the exercise instructions
   - Record the exercise source code (the placeholder content)
   - Look for `ALTER SESSION SET QUERY_TAG` — extract the exercise number/ID
3. Determine which notebook this is (HOL exercise notebook vs solution vs other)

#### For SQL files (.sql):
1. Read the file
2. Find blocks with `-- YOUR CODE HERE`
3. Read the surrounding SQL comments — they often contain exercise instructions
4. Note any QUERY_TAG patterns

#### For Solution files:
1. If solution notebooks exist, read them and match cells by name to exercise cells
2. If solution SQL files exist, read them for matching exercise blocks
3. Record the complete solution code for each matched exercise

#### For README/Documentation:
1. Read for workshop metadata: name, description, audience, duration
2. Look for schedule/timeline information
3. Look for exercise reference tables

#### For Build Scripts (if present):
1. Read for exercise/solution definitions
2. Extract module/notebook organization
3. This is a bonus signal — the analysis should work WITHOUT a build script

### Phase 4: Synthesis

**Goal**: Compile findings into a structured report for the author.

Organize the discovered exercises into modules (one per notebook or logical group). For each exercise, record:
- Exercise number/ID
- Cell name (if available)
- Parent notebook/file
- Exercise title (from instructions markdown)
- Concept being taught (inferred from instructions)
- Whether a matching solution was found
- Key Snowflake functions or technology patterns used (if detectable)
- Whether progress tracking is instrumented

Present the findings as a structured summary:

```
Workshop Analysis Report
========================
Repository: [path]

Detected Structure:
  Notebooks: [count] HOL + [count] solutions
  SQL scripts: [count] files
  Build script: [found/not found]
  Existing tutor: [found/not found]
  Existing AGENTS.md: [found/not found]

Exercises Found: [total]
  Module 1: [title] ([notebook], exercises [range])
    Ex [N]: [cell_name] — "[concept]"
    Ex [N]: [cell_name] — "[concept]"
    ...
  Module 2: [title] ([notebook], exercises [range])
    ...

Solutions: [matched]/[total] exercises matched
Progress Tracking: [detected/not detected]
Snowflake Functions / Key Patterns: [list of detected functions]

Warnings:
  - [any issues: missing solutions, ambiguous exercises, etc.]

Does this look correct? Any exercises I missed or miscategorized?
```

### Phase 5: Ambiguity Handling

If the exploration cannot confidently identify exercises:

- **No `YOUR CODE HERE` markers found**: Ask the user: "I couldn't find exercise placeholders. Which files contain the exercises your participants work on? Do you use a different marker?"
- **Notebooks found but unclear which are HOL vs solution**: Ask: "I found multiple notebooks. Which ones are the participant-facing exercises and which are solutions?"
- **No solution files found**: Report this as a warning, not an error: "No solution files found. The tutor will still work with L1/L2 hints from exercise instructions, but L3 (full solution) hints won't be available. Consider adding a solutions directory for the best tutor experience."
- **Ambiguous module grouping**: Ask: "How should I group these exercises into modules?"

**STOP**: Wait for the author to confirm the analysis before proceeding to GENERATE.

## Output

The analysis produces a mental model of the workshop that the GENERATE sub-skill uses to fill templates. The structured findings are NOT written to a file at this stage — they exist in the conversation context. The GENERATE sub-skill persists them as `workshop.yaml`.

## Error Handling

- **Empty repository**: "This directory doesn't appear to contain workshop content. I found no notebooks, SQL files, or exercise markers. Are you in the right directory?"
- **Read errors**: If a notebook file is too large or malformed, report the error and skip that file, continuing with others.
- **No exercises at all**: "I found workshop files but no exercises. This might be a reference-only repository. Would you like to proceed anyway, or point me to where the exercises are?"
