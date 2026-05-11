---
name: daily-note
description: "Create or update today's Obsidian daily note with meeting blocks from iCal. Use this skill whenever the user mentions: daily note, prep my day, today's meetings, meeting notes for today, set up my day, daily prep, tagesnotiz, or any request to prepare/view/update their daily schedule in Obsidian. Also trigger when the user asks to sync calendar events into notes."
---

# Daily Note: iCal → Obsidian

Fetch today's calendar events from macOS Calendar (iCal) and create or update a daily note in the user's Obsidian vault. The note contains a `# Meeting Notes` section with one `##` block per meeting, sorted chronologically. Existing content is never overwritten — only new meetings are inserted.

## Configuration

This skill needs a few user-specific settings. Check memory for entries prefixed with `daily-note skill:`. If any are missing, ask the user before proceeding:

| Setting | Memory key | Example |
|---------|-----------|---------|
| Obsidian vault path | `daily-note skill: Obsidian vault path` | `/Users/me/my-vault/` |
| Timezone | `daily-note skill: Timezone` | `Europe/Zurich` |
| Work email domain | `daily-note skill: Work email domain` | `@example.com` |

Use these values everywhere the skill references vault path, timezone, or email domain.

## Prerequisites

### MCP Server Required

| Server | Purpose |
|--------|---------|
| `mcp-ical` | Read calendar events from macOS Calendar |

Test with:
```python
call_tool('mcp__mcp-ical__list_calendars', {})
```

If it fails, help the user install the mcp-ical server.

## Workflow

### Step 1: Fetch Today's Events

Query iCal for today's events:

```python
from datetime import date
today = date.today().isoformat()
call_tool('mcp__mcp-ical__list_events', {
    'start_date': f'{today}T00:00:00',
    'end_date': f'{today}T23:59:59'
})
```

**Filter the results:**

- **Include only work calendars.** List calendars first with `mcp__mcp-ical__list_calendars` if unsure which are work calendars. Exclude personal, holiday, and birthday calendars.
- **Skip all-day events** — they don't need meeting note templates.
- **Skip private events** — events marked as private/confidential should not appear in the note.
- **Skip declined and cancelled events** — only include events the user has accepted or tentatively accepted.

**Sort** remaining events by start time ascending.

**Format times** in 24-hour format (`HH:MM`), using the configured timezone. The iCal MCP returns ISO8601 timestamps — convert them to local time. The system clock is already in the correct timezone, so parsing the time component directly is usually sufficient.

### Step 2: Read or Initialize the Daily Note

The daily note lives at:
```
<vault-path>/YYYY-MM-DD.md
```

**If the file exists:** read it and proceed to Step 3.

**If the file doesn't exist:** start with this skeleton:

```markdown
---
title: "YYYY-MM-DD"
tags: [daily]
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: daily
---

# Meeting Notes

```

### Step 3: Parse Existing Meetings

Look within the `# Meeting Notes` section for existing `## HH:MM |` headings. Everything between one `## HH:MM |` heading and the next (or end of section) belongs to that meeting and is untouched.

Build a list of already-present meeting titles (the text after `## HH:MM | `). These will be skipped when inserting new events.

**Section boundary rules:**
- The `# Meeting Notes` section starts at the `# Meeting Notes` heading.
- It ends at the next `# ` heading (another H1) or end of file.
- Content outside this section (above or below) is never modified.

**If the file exists but has no `# Meeting Notes` section:** insert `# Meeting Notes` after the frontmatter (after the closing `---`), before any existing content.

**If the file has frontmatter missing:** prepend the standard frontmatter block.

### Step 4: Build and Insert New Meeting Blocks

For each calendar event not already in the note:

1. **Check if the meeting is internal.** Look at the attendees list from the iCal event. If every attendee has the configured work email domain, append `(Internal)` to the heading. If any attendee has a different domain, it's an external meeting — no tag. If there are no attendees (e.g., a personal block), treat it as internal.

2. **Apply wikilinks** to the meeting title. Use best-effort judgment to link recognized entities:
   - Well-known technology and product names: `[[Snowflake]]`, `[[Cortex]]`, `[[Streamlit]]`, `[[dbt]]`, `[[Iceberg]]`
   - Company/partner/customer names you recognize from context (e.g., `[[Swisscom]]`, `[[SBB]]`, `[[Accenture]]`, `[[Microsoft]]`)
   - Don't over-link — only wikilink proper nouns that are clearly entity names, not generic words

3. **Generate the meeting block:**

```markdown
## HH:MM | Meeting Title with [[Entity]] (Internal)

### Notes

### Action Items
- [ ] 
```

The `(Internal)` tag only appears when all attendees share the configured work email domain. External meetings omit it.

4. **Insert chronologically** within the `# Meeting Notes` section. If existing meetings are at 10:00 and 14:00 and a new meeting is at 12:00, insert it between them.

**Matching logic for skipping duplicates:** Compare the meeting title (ignoring the time prefix and wikilink brackets). A meeting called "Swisscom Sync" matches an existing `## 14:00 | [[Swisscom]] Sync` heading. Be flexible with minor variations — the goal is to avoid duplicates, not enforce exact string matching.

### Step 5: Write the Note and Confirm

1. Update the `updated` field in frontmatter to today's date.
2. Write the assembled note to `<vault-path>/YYYY-MM-DD.md`.
3. Report to the user:
   - How many meetings were found in the calendar
   - How many were newly added to the note
   - How many were already present (skipped)
   - List the meeting schedule for quick reference

**Example confirmation:**
```
Daily note updated: <vault-path>/2026-04-27.md

Found 5 meetings today:
- 09:00 | Weekly Team Standup (added)
- 10:30 | SBB Architecture Review (added)
- 12:00 | Lunch & Learn (skipped — already in note)
- 14:00 | Swisscom Sync (skipped — already in note)
- 16:00 | Cortex Code Exchange with Devoteam (added)

3 added, 2 already present.
```

## Meeting Block Template

Use this exact structure for every meeting. Don't add extra fields (no attendees, no links, no duration). Keep it minimal so the user fills in what matters during the meeting.

```markdown
## HH:MM | Meeting Title (Internal)

### Notes

### Action Items
- [ ] 
```

The `(Internal)` tag appears only when all attendees share the configured work email domain. Omit it for external meetings.

## Technical Notes

### Time Parsing
iCal returns times like `2026-04-27T09:00:00+02:00`. Extract the hour and minute from the local time component. If the offset indicates a different timezone, convert to the configured timezone first.

### Frontmatter Format
```yaml
---
title: "YYYY-MM-DD"
tags: [daily]
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: daily
---
```

The `created` date should be set only once (when the note is first created). The `updated` date changes every time the skill runs.

### Wikilink and Internal Tag Examples
| Calendar Title | Attendees | Rendered |
|---|---|---|
| Weekly Sync with Swisscom | mix of internal and external domains | `## 09:00 \| Weekly Sync with [[Swisscom]]` |
| Cortex Demo for SBB | mix of internal and external domains | `## 14:00 \| [[Cortex]] Demo for [[SBB]]` |
| Internal Team Standup | all internal domain | `## 10:00 \| Internal Team Standup (Internal)` |
| dbt Migration Planning | all internal domain | `## 11:00 \| [[dbt]] Migration Planning (Internal)` |
| 1:1 Anton / Christian | all internal domain | `## 14:30 \| 1:1 Anton / Christian (Internal)` |

### Edge Cases
- **No meetings today:** Create the note with frontmatter and an empty `# Meeting Notes` section. Tell the user "No meetings found for today."
- **All meetings already in note:** Don't modify the file. Tell the user "All meetings already present, nothing to add."
- **Overlapping times:** Multiple meetings at the same start time are fine — insert them both at that position.
