---
name: event-sync
description: "Sync marketing events from a Google Sheet to an Apple/Google Calendar. Reads a sheet tab, filters by region, web-searches event details, and creates calendar entries with HTML-formatted descriptions. Use when: sync events, sheet to calendar, event sync, marketing calendar, import events from sheet."
---

# Event Sync: Google Sheets → Calendar

Sync field marketing events from a Google Sheets planning tracker into an Apple Calendar (which syncs to Google Calendar). Each event gets a country flag emoji title, a web-searched description, and HTML-formatted organizer/audience/sign-up details.

## Prerequisites

### MCP Servers Required

| Server | Purpose | Install |
|--------|---------|---------|
| `google-workspace` | Read Google Sheets | Bundled with Cortex Code |
| `mcp-ical` | Create/update Apple Calendar events | See `references/mcp-setup.md` |

**Check availability:**

```python
# Test google-workspace
call_tool('mcp__google-workspace__get_spreadsheet_info', {'spreadsheet_id': '<SPREADSHEET_ID>'})

# Test mcp-ical
call_tool('mcp__mcp-ical__list_calendars', {})
```

If either fails, **load** `reference/mcp-setup.md` and help the user install.

## Workflow

### Step 1: Gather Parameters

**Ask** the user:

```
To sync events from your Google Sheet to a calendar:

1. **Sheet URL**: Paste the Google Sheets URL
2. **Tab name**: Which sheet tab contains the events? (e.g. "FY27 DACH")
3. **Region filter**: Which regions to include? (e.g. "CH, AT" or "CH, AT, DACH")
4. **Target calendar**: Name of the Apple Calendar to sync to (e.g. "Snowflake Alps Events")
5. **Time filter**: Future only, past only, or all events?
```

Extract the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/...`

**⚠️ STOP**: Confirm parameters before proceeding.

### Step 2: Read & Filter (Dry Run)

**Actions:**

1. Read the sheet:
```python
import json
raw = call_tool('mcp__google-workspace__read_spreadsheet', {
    'spreadsheet_id': '<SPREADSHEET_ID>',
    'range': "'<TAB_NAME>'!A1:W939"
})
data = json.loads(raw)  # CRITICAL: returns JSON string, not array
```

2. Identify columns from header row (row 1 or 2). Expected columns:
   - **From** / **To**: dates in `dd-Mon` format (e.g. `23-Apr`)
   - **Region**: contains emoji flags (🇨🇭, 🇦🇹, 🇩🇪🇦🇹🇨🇭 DACH, etc.)
   - **Location**: city name (fallback for region detection)
   - **Status**: skip if `canceled`
   - **Initiative**: event name

3. Filter events by region. Match using:
   - Emoji flags in region column: `🇨🇭` for Switzerland, `🇦🇹` for Austria, `🇩🇪🇦🇹🇨🇭` for DACH
   - City names in location as fallback (Zurich, Geneva, Vienna, etc.)

4. Parse dates with FY year inference:
   - FY27 = Feb 2026 – Jan 2027
   - `dd-Mon` → `datetime.strptime(f"{d.strip()}-2026", "%d-%b-%Y")`

5. Apply time filter (future/past/all relative to today).

6. Present filtered events as a table:

```
| # | Date | Flag | Event Name | Location | Status |
|---|------|------|------------|----------|--------|
| 1 | Apr 23 | 🇨🇭 | WiDS Geneva | Geneva | Planned |
```

**⚠️ STOP**: User must approve the event list before creating calendar entries.

### Step 3: Enrich & Create Events

For each approved event:

1. **Web search** for the event: `web_search("<EVENT_NAME> <YEAR> <CITY>")`
2. Extract: short description, organizer, audience (if Snowflake organizes), sign-up link
3. If info not found, use `TBD`
4. **Create calendar event** with HTML formatting:

```python
call_tool('mcp__mcp-ical__create_event', {
    'create_event_request': {
        'title': '<FLAG> <EVENT_NAME>',
        'start_time': '<YYYY-MM-DD>T09:00:00',
        'end_time': '<YYYY-MM-DD>T18:00:00',
        'all_day': True,
        'calendar_name': '<CALENDAR_NAME>',
        'location': '<CITY>, <COUNTRY>',
        'notes': '<DESCRIPTION>\n\n<b>Organizer:</b> <ORG>\n<b>Audience:</b> <AUD>\n<b>Sign-Up link:</b> <a href="<URL>"><LINK_TEXT></a>'
    }
})
```

**Formatting rules:**
- Use `<b>...</b>` for bold (NOT Markdown `**...**`)
- Use `<a href="URL">text</a>` for clickable links
- Use `\n\n` for paragraph breaks
- Flag emoji: 🇨🇭 Switzerland, 🇦🇹 Austria, 🇩🇪🇦🇹🇨🇭 DACH

### Step 4: Verify

List events from the target calendar:

```python
call_tool('mcp__mcp-ical__list_events', {
    'calendar_name': '<CALENDAR_NAME>',
    'from_date': '<START_DATE>',
    'to_date': '<END_DATE>'
})
```

Present a summary: total events created, any failures, date range covered.

## Stopping Points

- ✋ After Step 1: Parameters confirmed
- ✋ After Step 2: Event list approved (dry run)

## Technical Notes

### JSON Parsing Gotcha
`mcp__google-workspace__read_spreadsheet` returns a **JSON string**, not a Python list. Always `json.loads()` before iterating.

### Emoji Region Matching
Region column contains flag emojis + text (e.g. `🇨🇭 Switzerland`). Use `in` operator: `'🇨🇭' in region`.

### HTML vs Markdown in Calendar Notes
- Apple Calendar/iCal: plain text only, auto-detects bare URLs
- Google Calendar: renders HTML tags (`<b>`, `<a href>`, `<br>`)
- Always use HTML tags so Google Calendar renders rich text

### Multi-day Events
Set `all_day: True` with different start/end dates for multi-day events.

## Output

Calendar populated with enriched, HTML-formatted events from the Google Sheet.
