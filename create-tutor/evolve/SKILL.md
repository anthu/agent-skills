---
name: evolve
description: "Sub-skill for updating tutor infrastructure after workshop content changes or author feedback."
---

# Evolve Tutor

This sub-skill updates an existing tutor when workshop content changes or the author provides feedback. It re-explores the repo, diffs against the existing `workshop.yaml`, and regenerates affected sections.

## Prerequisites

- A `workshop.yaml` exists in the workshop root (from a previous GENERATE run)
- The tutor pedagogy reference (`reference/tutor-pedagogy.md`) is loaded

## Two Modes

### Mode A: Content Changed

The author has modified exercises, added notebooks, renamed cells, or updated solutions. The tutor needs to be brought in sync.

### Mode B: Feedback-Driven

The author wants to improve specific parts of the tutor based on workshop experience (e.g., "Exercise 4 hints are too vague", "Students keep getting a warehouse error").

Detect the mode from the user's prompt. If ambiguous, ask.

---

## Mode A: Content Changed

### Step 1: Re-Explore

Run the full agentic exploration defined in `analyze/SKILL.md` (Phases 1-3). Load that file and follow its Broad Discovery, Content Detection, and Deep Read phases exactly — this ensures EVOLVE and ANALYZE always use the same exploration logic and stay in sync:
- Phase 1: Glob for all workshop files
- Phase 2: Grep for exercise markers, QUERY_TAG patterns, key functions
- Phase 3: Read exercise cells, instructions, and solutions

### Step 2: Load Existing Manifest

Read the existing `workshop.yaml` from the workshop root. This represents the state of the tutor when it was last generated.

### Step 3: Diff

Compare the new exploration results against the existing manifest. Identify:

- **New exercises**: Present in the current content but not in the manifest
- **Removed exercises**: In the manifest but no longer found in the content
- **Changed exercises**: Same cell name but different solution code, or instructions updated
- **Renamed cells**: Cell name changed (detected by matching content/position)
- **New modules**: New notebook added
- **Removed modules**: Notebook deleted
- **Changed metadata**: Workshop name, description, or other metadata updated

### Step 4: Present Diff

Show the author what changed:

```
Tutor Update Report
====================

Changes detected since last generation:

+ NEW: Exercise 12 (p3_ex12_dashboard) in hol_03
  Concept: "Build a Streamlit dashboard for the agent"

~ CHANGED: Exercise 7 — solution updated
  Previous: Used TRY_PARSE_JSON pattern
  Current: Uses response_format structured output

~ CHANGED: Exercise 3 — instructions expanded
  Added new markdown section with code examples

- REMOVED: Exercise 8 — no longer has YOUR CODE HERE marker
  (Cell still exists but is now pre-built)

Unchanged: Exercises 1-6, 9-11

Shall I regenerate the tutor skill and AGENTS.md?
```

**STOP**: Wait for the author to approve before making changes.

### Step 5: Regenerate

On approval:
1. Update `workshop.yaml` with the new analysis
2. Regenerate hints for new and changed exercises
3. Update the tutor SKILL.md (exercise list, hints, triage logic)
4. Update AGENTS.md (exercise reference table)
5. Present the updated hints for new/changed exercises in a focused report

For unchanged exercises, preserve the existing hints in `workshop.yaml` — they may have been manually refined by the author.

---

## Mode B: Feedback-Driven

The author provides specific feedback. Handle these common patterns:

### "Improve hints for Exercise N"

1. Read the current hints from `workshop.yaml`
2. Read the exercise instructions and solution
3. Generate improved hints based on the feedback
4. Present the before/after for review
5. On approval, update `workshop.yaml` and the tutor SKILL.md

### "Add an environment error"

1. Ask for the error pattern and fix (if not provided)
2. Add to the `environment.errors` section of `workshop.yaml`
3. Add to the Common Environment Errors section of the tutor SKILL.md
4. Confirm the addition

### "Students are struggling with Exercise N"

1. Analyze the exercise: read instructions, solution, current hints
2. Suggest improvements:
   - More detailed L1 hint with concrete reference to common mistakes
   - Better L2 code skeleton
   - Additional context in the exercise instructions
3. Present suggestions for review
4. On approval, update the tutor

### "I renamed/moved files"

Treat as Mode A — re-explore and diff.

### General Refinement

For any other feedback:
1. Understand what the author wants changed
2. Make the specific change to `workshop.yaml` and/or the tutor SKILL.md
3. Present the change for review
4. Apply on approval

## Output

Updated versions of:
- `workshop.yaml`
- `.snowflake/cortex/skills/tutor/SKILL.md`
- `AGENTS.md` (if exercise reference changed)

## Error Handling

- **No workshop.yaml found**: "I can't find an existing workshop.yaml. Run ANALYZE + GENERATE first to create the initial tutor, then use EVOLVE for updates."
- **Manifest out of sync**: If the manifest references files that no longer exist, flag them clearly in the diff.
- **Merge conflicts**: If the author has manually edited the tutor SKILL.md, warn before overwriting: "The tutor SKILL.md appears to have been manually edited since the last generation. Regenerating will overwrite those changes. Proceed?"
