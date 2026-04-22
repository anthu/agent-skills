#!/usr/bin/env python3
"""
sync_events.py — Sync marketing events from a Google Sheet to an Apple/Google Calendar.

Uses the Cortex Code Agent SDK to read the sheet, web-search event details,
and create calendar entries with HTML-formatted descriptions.

Usage:
    uv run python sync_events.py \
        --sheet-url "https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0" \
        --tab "FY27 DACH" \
        --regions "CH,AT,DACH" \
        --calendar "Snowflake Alps Events" \
        --dry-run

Prerequisites:
    - Cortex Code CLI installed (curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh)
    - MCP servers configured (see references/mcp-setup.md):
        - google-workspace (bundled with Cortex Code)
        - mcp-ical (Apple Calendar)
    - Snowflake connection configured in ~/.snowflake/connections.toml
"""

import argparse
import asyncio
import re
import sys

from cortex_code_agent_sdk import (
    AssistantMessage,
    CortexCodeAgentOptions,
    ResultMessage,
    query,
)

REGION_MAP = {
    "CH": "🇨🇭",
    "AT": "🇦🇹",
    "DE": "🇩🇪",
    "DACH": "🇩🇪🇦🇹🇨🇭",
}


def extract_spreadsheet_id(url: str) -> str:
    """Extract spreadsheet ID from a Google Sheets URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        print(f"Error: Could not extract spreadsheet ID from URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1)


def build_prompt(
    spreadsheet_id: str,
    tab: str,
    regions: list[str],
    calendar: str,
    dry_run: bool,
    time_filter: str,
) -> str:
    region_flags = ", ".join(
        f"{REGION_MAP.get(r.upper(), r)} ({r})" for r in regions
    )

    if dry_run:
        action_instructions = """
ACTION: DRY RUN ONLY
- Present a markdown table of all matching events with columns: #, Date, Flag, Event Name, Location, Status
- Do NOT create any calendar events
- Print the total count at the end
"""
    else:
        action_instructions = f"""
ACTION: CREATE EVENTS
- For each matching event, web-search for details (description, organizer, sign-up link)
- Create each event in the "{calendar}" calendar using mcp__mcp-ical__create_event
- Title format: <flag_emoji> <event_name>
- Use HTML formatting in notes: <b>Organizer:</b>, <b>Audience:</b>, <a href="URL">Sign-Up link</a>
- If details not found, use "TBD"
- Set all_day: true for all events
- After creating all events, list them from the calendar to verify
"""

    return f"""You are syncing marketing events from a Google Sheet to a calendar.

SPREADSHEET ID: {spreadsheet_id}
SHEET TAB: {tab}
REGION FILTER: {region_flags}
TARGET CALENDAR: {calendar}
TIME FILTER: {time_filter}

STEPS:
1. Read the sheet using mcp__google-workspace__read_spreadsheet with range "'{tab}'!A1:W939"
   CRITICAL: The result is a JSON string. You MUST json.loads() it before iterating.

2. Identify the header row and find columns for: From, To, Region, Location, Status, Initiative

3. Filter rows where:
   - Region column contains any of these emoji flags: {region_flags}
   - OR Location contains a city from Switzerland (Zurich, Geneva, Lausanne, Basel, Bern, Interlaken, Lucerne, Gland)
     or Austria (Vienna, Wien, Graz, Salzburg, Innsbruck, Linz, Stegersbach)
   - Status is NOT "canceled" (case-insensitive)
   - Has a valid date in the From column (dd-Mon format, e.g. "23-Apr")

4. Parse dates: dd-Mon format with year 2026 (FY27 = Feb 2026 - Jan 2027).
   Apply time filter: {time_filter} (relative to today).

{action_instructions}
"""


async def main():
    parser = argparse.ArgumentParser(
        description="Sync marketing events from Google Sheets to Apple/Google Calendar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run — list events without creating them
  uv run python sync_events.py \\
      --sheet-url "https://docs.google.com/spreadsheets/d/ABC123/edit" \\
      --tab "FY27 DACH" --regions "CH,AT,DACH" \\
      --calendar "Snowflake Alps Events" --dry-run

  # Create future events only
  uv run python sync_events.py \\
      --sheet-url "https://docs.google.com/spreadsheets/d/ABC123/edit" \\
      --tab "FY27 DACH" --regions "CH,AT" \\
      --calendar "My Events" --time-filter future

  # Sync all events (past + future)
  uv run python sync_events.py \\
      --sheet-url "https://docs.google.com/spreadsheets/d/ABC123/edit" \\
      --tab "FY27 DACH" --regions "CH,AT,DACH" \\
      --calendar "Snowflake Alps Events" --time-filter all
""",
    )
    parser.add_argument(
        "--sheet-url",
        required=True,
        help="Google Sheets URL (the spreadsheet ID is extracted automatically)",
    )
    parser.add_argument(
        "--tab",
        required=True,
        help="Sheet tab name (e.g. 'FY27 DACH')",
    )
    parser.add_argument(
        "--regions",
        required=True,
        help="Comma-separated region codes: CH, AT, DE, DACH (e.g. 'CH,AT,DACH')",
    )
    parser.add_argument(
        "--calendar",
        required=True,
        help="Target Apple Calendar name (e.g. 'Snowflake Alps Events')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matching events without creating calendar entries",
    )
    parser.add_argument(
        "--time-filter",
        choices=["future", "past", "all"],
        default="all",
        help="Filter events by time: future, past, or all (default: all)",
    )
    parser.add_argument(
        "--connection",
        default=None,
        help="Snowflake connection name (default: use CLI default)",
    )

    args = parser.parse_args()

    spreadsheet_id = extract_spreadsheet_id(args.sheet_url)
    regions = [r.strip() for r in args.regions.split(",")]

    prompt = build_prompt(
        spreadsheet_id=spreadsheet_id,
        tab=args.tab,
        regions=regions,
        calendar=args.calendar,
        dry_run=args.dry_run,
        time_filter=args.time_filter,
    )

    mode = "DRY RUN" if args.dry_run else "SYNC"
    print(f"[event-sync] Mode: {mode}")
    print(f"[event-sync] Sheet: {spreadsheet_id} / tab: {args.tab}")
    print(f"[event-sync] Regions: {', '.join(regions)}")
    print(f"[event-sync] Calendar: {args.calendar}")
    print(f"[event-sync] Time filter: {args.time_filter}")
    print("---")

    # Permission bypass is required for non-interactive (headless) execution.
    # The script reads Google Sheets data and creates calendar events without
    # user confirmation prompts. Only run this with trusted sheet URLs.
    options = CortexCodeAgentOptions(
        cwd=".",
        permission_mode="bypassPermissions",
        allow_dangerously_skip_permissions=True,
    )
    if args.connection:
        options.connection = args.connection

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="")
        elif isinstance(message, ResultMessage):
            print(f"\n\n[event-sync] Done: {message.subtype}")


if __name__ == "__main__":
    asyncio.run(main())
