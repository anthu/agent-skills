---
name: sync-projects
description: "Generate Obsidian project documentation from AI conversation history. Use when the user wants to organize their Cortex Code or Claude Code conversations into project notes, summarize what was worked on across sessions, or update project documentation with recent conversations. Triggers: sync projects, update projects, organize conversations, document projects, conversation history, project notes."
allowed-tools: [Bash, Read, Write]
---

# Sync Projects

Organize AI conversation history into Obsidian project notes with LLM-generated summaries.

## What This Skill Does

Reads conversation transcripts from Cortex Code (`~/.snowflake/cortex/conversations/`) and Claude Code (`~/.claude/projects/`), groups them by project (working directory), and generates rich Obsidian notes documenting:
- What was accomplished across all conversations
- Key decisions made
- Chronological conversation timeline with summaries

**Why this is a skill:** The LLM understands conversation content and writes meaningful summaries. A Python helper handles the deterministic file I/O, state tracking, and project matching.

---

## Workflow

Follow these five steps in order:

### Step 1: Discover Existing Projects

Run the helper script to see what project notes already exist:

```bash
python3 scripts/sync_projects.py --list-projects \
  --vault ~/ahuck-vault
```

This returns JSON with existing projects and their registered `working_directories`. These directories act as the "config" — the script matches conversation sessions to projects by longest-prefix matching on the working directory path.

**Why this matters:** You need to know what projects exist so you can understand where new conversations will land, and whether you need to create new projects.

### Step 2: Find Unprocessed Conversations

Get the list of conversation sessions not yet documented:

```bash
python3 scripts/sync_projects.py --list-new \
  --vault ~/ahuck-vault
```

This scans both Cortex and Claude Code conversation sources and returns JSON for each unprocessed session:
- `session_id`: unique identifier
- `source`: "Cortex (connection_name)" or "Claude Code"
- `working_dir`: where the conversation took place
- `title`: first user message (truncated to 80 chars)
- `date`: ISO 8601 date when conversation started
- `file_path`: full path to the conversation transcript file

**Why this matters:** The script tracks which sessions have already been processed in `vault/projects/.processed_sessions.json`. You only need to read and summarize new conversations, making incremental runs fast.

### Step 3: Read and Summarize Each Conversation

For each unprocessed session, read the full transcript from `file_path` and write a substantive 1-3 sentence summary.

**What makes a good summary:**
- Captures what was **accomplished** or **decided**, not just what was discussed
- Specific: mentions file names, tools used, problems solved
- Avoids generic phrases like "discussed the project" or "worked on features"

**Examples:**

❌ Bad: "Discussed database optimization"  
✅ Good: "Profiled `snow dcm plan` performance; identified 8-minute build time caused by redundant SQL queries in 14 dbt source models"

❌ Bad: "Fixed git issues"  
✅ Good: "Resolved GPG signing failure by switching to key pair authentication; re-signed 12 commits on `main` branch"

**Read strategically:** Long conversations (500+ messages) — focus on the first 50-100 messages and the last 20-30 to understand the goal and outcome. Tool call results often contain the substance.

### Step 4: Update Project Notes

For each session with its summary, run:

```bash
python3 scripts/sync_projects.py --update <session_id> \
  --vault ~/ahuck-vault \
  --working-dir "<working_directory>" \
  --title "<conversation_title>" \
  --date "YYYY-MM-DD" \
  --source "<source>" \
  --summary "<your 1-3 sentence summary>"
```

**What the script does:**
1. Matches the session to an existing project (longest-prefix match on `working_dir`)
2. If no match: creates a new project note from the template, auto-naming it based on the path
3. Adds the session to the project's `## Conversation Timeline` table (inside HTML comment markers)
4. Updates frontmatter: `date_end`, `session_count`
5. Marks the session as processed in `.processed_sessions.json`

**Why HTML comments:** Only the `<!-- AUTO-CONVERSATIONS-START -->` to `<!-- AUTO-CONVERSATIONS-END -->` block is managed by the script. Everything else (Overview, Accomplishments, Decisions sections) is preserved, allowing users to manually curate those sections without the script overwriting their edits.

### Step 5: Report Results

Tell the user:
- How many project notes were updated
- How many new projects were created
- Total number of sessions processed

**Example output:**
```
Updated 8 project notes with 111 new conversations.
- PSE Intelligence System: 45 sessions
- Paperclip Multi-Agent: 38 sessions  
- Geocode Benchmark: 3 sessions
... (etc)

3 new projects created:
- Dev-Environment-Tooling (10 sessions)
- SDS26-Workshop (4 sessions)
- Frosty-Security-Review (2 sessions)
```

---

## Project Note Format

Each generated note in `vault/projects/` follows this structure:

```markdown
---
title: "Project Name"
type: project
status: active
date_start: YYYY-MM-DD
date_end: YYYY-MM-DD
tags: [project, ...]
working_directories:
  - /path/to/working/dir
session_count: N
---

## Overview
_Human-editable description_

## Working Directories
- `/path/to/working/dir` — ✅ exists

## What Was Accomplished
_Human-curated achievements_

## Notable Decisions
_Human-curated key decisions_

<!-- AUTO-CONVERSATIONS-START -->
## Conversation Timeline
| Date | Summary | Source | Dir |
|------|---------|--------|-----|
| 2026-04-01 | Summary text | Cortex (ahuck) | ✅ |
<!-- AUTO-CONVERSATIONS-END -->
```

**Key Points:**
- Only the Conversation Timeline table (between HTML comments) is auto-managed
- Overview, Accomplishments, and Decisions sections are never touched by the script
- Users can manually curate those sections to build a comprehensive project history

---

## Helper Script Modes

The `scripts/sync_projects.py` script has three modes:

### Mode 1: List Projects
```bash
python3 scripts/sync_projects.py --list-projects --vault <path>
```
Returns JSON array of existing projects with their registered `working_directories`.

### Mode 2: List New Sessions
```bash
python3 scripts/sync_projects.py --list-new --vault <path>
```
Returns JSON array of unprocessed conversation sessions from both Cortex and Claude Code sources.

### Mode 3: Update Project
```bash
python3 scripts/sync_projects.py --update <session_id> \
  --vault <path> \
  --working-dir "<dir>" \
  --title "<title>" \
  --date "YYYY-MM-DD" \
  --source "<source>" \
  --summary "<summary>"
```
Updates (or creates) a project note with the new session. Handles project matching, note creation from template, and state tracking.

---

## Examples

**Example 1: Fresh Run**
```
User: "Organize my Cortex and Claude Code conversations into project notes"

Step 1: python3 scripts/sync_projects.py --list-projects --vault ~/ahuck-vault
→ Returns: [] (no projects yet)

Step 2: python3 scripts/sync_projects.py --list-new --vault ~/ahuck-vault  
→ Returns: 244 unprocessed sessions

Step 3-4: For each session:
- Read transcript from file_path
- Summarize in 1-3 sentences
- Run --update with summary

Step 5: Report
→ "Created 8 project notes with 244 conversations"
```

**Example 2: Incremental Update**
```
User: "Update project docs with recent conversations"

Step 1: --list-projects
→ Returns: 8 existing projects

Step 2: --list-new
→ Returns: 12 new sessions (since last run)

Step 3-4: Process only the 12 new sessions

Step 5: Report
→ "Updated 3 project notes with 12 new conversations. 0 new projects created."
```

---

## Notes

- **Resumed conversations:** Cortex and Claude Code can resume the same conversation across multiple sessions. The script uses `session_id` to detect this and skip already-processed sessions.
- **Project matching:** Longest-prefix match on `working_dir`. Path `~/projects/work/skills/pse` matches project with `working_directories: ["~/projects/work"]`.
- **Auto-naming:** New projects are named from the last path segment. `~/git/new-tool` → "New-Tool.md"
- **Directory validation:** Script checks if each `working_directory` exists on disk and displays ✅ (exists) or ❌ (not found) in the note.

---

## Troubleshooting

**Script fails with "No module named yaml":**
- The script uses only Python stdlib (json, os, pathlib, argparse, datetime, re). No external dependencies required.

**Sessions not appearing as "new":**
- Check `vault/projects/.processed_sessions.json` — delete it to reprocess all sessions.

**Project note frontmatter not recognized by Obsidian:**
- Verify YAML is valid: `working_directories` must be a list, dates must be YYYY-MM-DD format.

**Summaries are generic:**
- Read deeper into the conversation transcript. Focus on tool call results and the last 20-30 messages to see what was actually accomplished.
