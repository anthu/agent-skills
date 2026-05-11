---
name: create-tutor
description: >
  Meta-skill that generates an AI tutor for any Cortex Code workshop.
  Agentically explores existing notebooks, SQL scripts, and solutions to
  produce a tutor skill with graduated hints (concept -> structure ->
  solution), error triage, and solution validation. Works with any folder structure — no conventions
  assumed. Use when: create tutor, generate tutor, workshop tutor, analyze
  workshop, evolve tutor, update tutor, add tutor to my workshop, make my
  workshop AI-tutored, tutored workshop, workshop skill, tutor skill,
  hands-on lab, HOL, Snowsight notebook tutor, AI_PARSE_DOCUMENT workshop,
  teaching assistant, workshop assistant, exercise hints, graduated hints.
  This skill CREATES tutor infrastructure — it does NOT tutor students
  directly. For student-facing help during a workshop, use the generated
  tutor skill. DO NOT attempt to build workshop tutors manually — invoke
  this skill first.
---

# Create Tutor

Generate an AI tutor for any hands-on workshop that uses Cortex Code.

## Setup (mandatory — do this FIRST)

**Load** `reference/tutor-pedagogy.md` BEFORE doing anything else. This contains the pedagogical theory behind graduated hints, triage logic, and solution validation. Every downstream sub-skill assumes you have already internalized this reference. If you skip it, the generated tutor will lack the core teaching patterns that make it effective.

## Intent Detection

| Intent | Triggers | Action |
|--------|----------|--------|
| ANALYZE | "create tutor", "analyze workshop", "generate tutor", "add tutor", "make tutored" | **Load** `analyze/SKILL.md` |
| GENERATE | "generate files", "produce tutor", "create the files", approved analysis | **Load** `generate/SKILL.md` |
| EVOLVE | "update tutor", "evolve", "refresh", "I changed exercises", "improve hints" | **Load** `evolve/SKILL.md` |

## Default Flow

If the user's intent is not clearly one of the three modes:

1. Check if `workshop.yaml` exists in the current directory
   - **Yes** → Default to **EVOLVE** (the workshop already has tutor infrastructure)
   - **No** → Default to **ANALYZE** (start fresh)

## What This Skill Produces

| Output | File | Purpose |
|--------|------|---------|
| Tutor skill | `.snowflake/cortex/skills/tutor/SKILL.md` | Participant-facing AI tutor with graduated hints |
| Workspace context | `AGENTS.md` | Routes error-fixing and validation to the tutor |
| Manifest | `workshop.yaml` | Machine checkpoint for evolving the tutor later |

## How It Works

The skill explores your workshop repository using Glob, Grep, and Read — the same agentic search pattern that powers Cortex Code itself. No rigid folder structure is assumed.

1. **ANALYZE** discovers exercises (by `YOUR CODE HERE` markers), solutions (by matching cell names), and workshop structure (from notebooks, SQL files, documentation)
2. **GENERATE** produces a tutor skill with L1/L2/L3 graduated hints, error triage, solution validation, and optionally progress tracking
3. **EVOLVE** re-explores after content changes and updates the tutor incrementally

Every mode has a mandatory **STOP** point where the author reviews before files are written.

## Stopping Points

- After ANALYZE: Review discovered exercises before generating anything
- After GENERATE: Review all generated files and AI-generated hints
- During EVOLVE: Review proposed changes before applying them
- Before overwriting existing AGENTS.md or tutor SKILL.md

## Error Handling

- **Empty directory**: Ask the user if they're in the right directory
- **No exercise markers found**: Ask the user which files contain exercises and what marker convention they use
- **No solutions found**: Proceed with L1/L2 hints only, warn that L3 requires solutions
- **workshop.yaml not found in EVOLVE mode**: Suggest running ANALYZE + GENERATE first
