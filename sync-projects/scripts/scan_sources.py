#!/usr/bin/env python3
"""
scan_sources.py — Simple scanner that lists all conversation files

Outputs JSON array with minimal metadata:
- session_id
- source (Cortex, Claude Code, Cursor)
- file_path (where to read the conversation)
- working_dir (if available from filename/metadata)
- date (if available)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

CORTEX_DIR = Path.home() / ".snowflake" / "cortex" / "conversations"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
CURSOR_PROJECTS_DIR = Path.home() / ".cursor" / "projects"


def scan_cortex() -> list:
    """Scan Cortex conversations (both CLI at top level and Desktop in subdirectories)."""
    if not CORTEX_DIR.exists():
        return []

    sessions = []
    for meta_file in CORTEX_DIR.glob("**/*.json"):
        if ".back." in meta_file.name or "history" in meta_file.name:
            continue
        if "images" in meta_file.parts:
            continue

        try:
            meta = json.loads(meta_file.read_text())
            session_id = meta.get("session_id", "")
            if not session_id:
                continue

            history_file = meta_file.parent / f"{meta_file.stem}.history.jsonl"
            if not history_file.exists():
                continue

            # Date: CLI uses ISO created_at, Desktop uses epoch creationDate
            date_str = ""
            created_at = meta.get("created_at", "")
            if created_at:
                date_str = created_at[:10]
            elif meta.get("creationDate"):
                try:
                    date_str = datetime.fromtimestamp(meta["creationDate"] / 1000).strftime("%Y-%m-%d")
                except:
                    pass

            connection = meta.get("connection_name", "")
            source = "Cortex Desktop" if not connection else f"Cortex ({connection})"

            sessions.append({
                "session_id": session_id,
                "source": source,
                "file_path": str(history_file),
                "working_dir": meta.get("working_directory", ""),
                "date": date_str,
            })
        except:
            continue

    return sessions


def scan_claude() -> list:
    """Scan Claude Code conversations - just list the files."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []

    sessions = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                # Try to extract session_id from first entry
                session_id = jsonl_file.stem
                working_dir = ""
                date = ""

                for line in jsonl_file.read_text().splitlines()[:20]:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            if entry.get("sessionId"):
                                session_id = entry["sessionId"]
                            if entry.get("cwd") and not working_dir:
                                working_dir = entry["cwd"]
                            if entry.get("timestamp") and not date:
                                date = entry["timestamp"][:10]
                        except:
                            pass

                sessions.append({
                    "session_id": session_id,
                    "source": "Claude Code",
                    "file_path": str(jsonl_file),
                    "working_dir": working_dir,
                    "date": date,
                })
            except:
                continue

    return sessions


def scan_cursor() -> list:
    """Scan Cursor conversations - just list the files."""
    if not CURSOR_PROJECTS_DIR.exists():
        return []

    sessions = []
    for project_dir in CURSOR_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        transcripts_dir = project_dir / "agent-transcripts"
        if not transcripts_dir.exists():
            continue

        # Infer working dir from project name
        project_name = project_dir.name
        if project_name.startswith("Users-"):
            working_dir = "/" + project_name.replace("-", "/", 2).replace("-", "/")
        else:
            working_dir = ""

        for session_dir in transcripts_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session_id = session_dir.name
            jsonl_file = session_dir / f"{session_id}.jsonl"

            if not jsonl_file.exists():
                continue

            try:
                # Get date from file mtime
                mtime = jsonl_file.stat().st_mtime
                date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

                sessions.append({
                    "session_id": session_id,
                    "source": "Cursor",
                    "file_path": str(jsonl_file),
                    "working_dir": working_dir,
                    "date": date,
                })
            except:
                continue

    return sessions


def main():
    print("Scanning conversation sources...", file=sys.stderr)

    cortex = scan_cortex()
    claude = scan_claude()
    cursor = scan_cursor()

    print(f"Found {len(cortex)} Cortex sessions", file=sys.stderr)
    print(f"Found {len(claude)} Claude Code sessions", file=sys.stderr)
    print(f"Found {len(cursor)} Cursor sessions", file=sys.stderr)

    all_sessions = cortex + claude + cursor
    print(f"Total: {len(all_sessions)} sessions\n", file=sys.stderr)

    # Output JSON
    print(json.dumps(all_sessions, indent=2))


if __name__ == "__main__":
    main()
