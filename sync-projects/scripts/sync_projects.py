#!/usr/bin/env python3
"""
sync_projects.py — Helper script for sync-projects skill

Three modes:
  --list-projects: List existing projects in vault
  --list-new: List unprocessed conversation sessions
  --update: Update a project note with a new session
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CORTEX_DIR = Path.home() / ".snowflake" / "cortex" / "conversations"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:60]

def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    
    yaml_text = parts[1].strip()
    result = {}
    
    # Simple YAML parser for our specific needs
    current_key = None
    
    for line in yaml_text.split("\n"):
        line = line.rstrip()
        if not line:
            continue
            
        if line.startswith("  - "):
            # List item
            if current_key and current_key in result:
                if not isinstance(result[current_key], list):
                    result[current_key] = [result[current_key]]
                result[current_key].append(line[4:].strip())
        elif ":" in line and not line.startswith(" "):
            # Key: value
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            if value.startswith("[") and value.endswith("]"):
                # Inline list
                items = value[1:-1].split(",")
                result[key] = [item.strip().strip('"').strip("'") for item in items if item.strip()]
            elif value:
                result[key] = value.strip('"').strip("'")
            else:
                # Empty value, might start a list
                current_key = key
                result[key] = []
    
    return result

def extract_text_from_content(content, skip_internal: bool = False) -> str:
    """Extract text from message content (handles both str and list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if skip_internal and block.get("internalOnly"):
                continue
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    return ""

def extract_title(messages: list, max_len: int = 80) -> str:
    """Derive a title from the first real user message."""
    for msg in messages:
        if msg.get("role") != "user":
            continue
        for skip in (True, False):
            text = extract_text_from_content(msg.get("content", ""), skip_internal=skip).strip()
            if not text:
                continue
            if re.match(r"^\s*<[^>]+>", text):
                continue
            if text.startswith("--- Skill:"):
                continue
            title = re.sub(r"\s+", " ", text)[:max_len]
            return title
    return "Untitled conversation"


# ---------------------------------------------------------------------------
# Mode 1: List Projects
# ---------------------------------------------------------------------------

def list_projects(vault_path: Path) -> list:
    """List existing projects in the vault."""
    projects_dir = vault_path / "projects"
    if not projects_dir.exists():
        return []
    
    projects = []
    for note_file in projects_dir.glob("*.md"):
        if note_file.name.startswith("."):
            continue
        
        try:
            content = note_file.read_text()
            frontmatter = parse_frontmatter(content)
            
            working_dirs = frontmatter.get("working_directories", [])
            if isinstance(working_dirs, str):
                working_dirs = [working_dirs]
            
            projects.append({
                "project_name": frontmatter.get("title", note_file.stem),
                "note_path": str(note_file.relative_to(vault_path)),
                "working_directories": working_dirs,
            })
        except (OSError, UnicodeDecodeError):
            continue
    
    return projects


# ---------------------------------------------------------------------------
# Mode 2: List New Sessions
# ---------------------------------------------------------------------------

def load_state(vault_path: Path) -> dict:
    """Load processed sessions state."""
    state_file = vault_path / "projects" / ".processed_sessions.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def _parse_cortex_meta(meta_file: Path) -> dict | None:
    """Parse a single Cortex conversation metadata file (CLI or Desktop)."""
    try:
        meta = json.loads(meta_file.read_text())
        session_id = meta.get("session_id", "")
        if not session_id:
            return None
        
        working_dir = meta.get("working_directory", "")
        connection = meta.get("connection_name", "")
        
        # Extract date — CLI uses ISO created_at, Desktop uses epoch creationDate
        date_str = ""
        created_at = meta.get("created_at", "")
        if created_at:
            try:
                date_str = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d")
            except:
                pass
        if not date_str and meta.get("creationDate"):
            try:
                date_str = datetime.fromtimestamp(meta["creationDate"] / 1000).strftime("%Y-%m-%d")
            except:
                pass
        
        # Desktop may have AI-generated title in metadata
        title = meta.get("title", "")
        
        # Extract title from history file if not already set
        history_file = meta_file.parent / f"{meta_file.stem}.history.jsonl"
        if history_file.exists():
            if not title:
                try:
                    messages = []
                    for line in history_file.read_text().splitlines()[:10]:
                        if line.strip():
                            try:
                                messages.append(json.loads(line))
                            except:
                                pass
                    if messages:
                        title = extract_title(messages)
                except:
                    pass
        
        if not title:
            title = "Untitled conversation"
        
        # Source label: Desktop sessions have null connection_name
        source = f"Cortex Desktop" if not connection else f"Cortex ({connection})"
        
        return {
            "session_id": session_id,
            "source": source,
            "working_dir": working_dir,
            "title": title,
            "date": date_str,
            "file_path": str(history_file),
        }
    except (json.JSONDecodeError, OSError):
        return None


def scan_cortex() -> list:
    """Scan Cortex conversations (both CLI at top level and Desktop in subdirectories)."""
    if not CORTEX_DIR.exists():
        return []
    
    sessions = []
    
    # Scan both top-level (CLI) and subdirectory (Desktop) .json files
    for meta_file in CORTEX_DIR.glob("**/*.json"):
        if ".back." in meta_file.name or "history" in meta_file.name:
            continue
        # Skip non-conversation directories like images/
        if "images" in meta_file.parts:
            continue
        
        result = _parse_cortex_meta(meta_file)
        if result:
            sessions.append(result)
    
    return sessions

def scan_claude() -> list:
    """Scan Claude Code conversations."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []
    
    sessions = []
    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        
        for jsonl_file in project_dir.glob("*.jsonl"):
            try:
                lines = jsonl_file.read_text().splitlines()
                if not lines:
                    continue
                
                # Parse first few lines for metadata
                session_id = ""
                cwd = ""
                timestamp = ""
                messages = []
                
                for line in lines[:20]:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        etype = entry.get("type", "")
                        
                        if etype in ("user", "assistant"):
                            if entry.get("isMeta") or entry.get("userType") == "internal":
                                continue
                            msg = entry.get("message", {})
                            messages.append({"role": msg.get("role", etype), "content": msg.get("content", "")})
                        
                        if not session_id and entry.get("sessionId"):
                            session_id = entry["sessionId"]
                        if not cwd and entry.get("cwd"):
                            cwd = entry["cwd"]
                        if not timestamp and entry.get("timestamp"):
                            timestamp = entry["timestamp"]
                    except:
                        continue
                
                if not session_id:
                    session_id = jsonl_file.stem
                
                date_str = ""
                if timestamp:
                    try:
                        date_str = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                    except:
                        pass
                
                title = extract_title(messages) if messages else "Untitled conversation"
                
                sessions.append({
                    "session_id": session_id,
                    "source": "Claude Code",
                    "working_dir": cwd,
                    "title": title,
                    "date": date_str,
                    "file_path": str(jsonl_file),
                })
            except (OSError, UnicodeDecodeError):
                continue
    
    return sessions

def list_new_sessions(vault_path: Path) -> list:
    """List unprocessed conversation sessions."""
    state = load_state(vault_path)
    
    cortex_sessions = scan_cortex()
    claude_sessions = scan_claude()
    all_sessions = cortex_sessions + claude_sessions
    
    # Filter out processed sessions
    new_sessions = [s for s in all_sessions if s["session_id"] not in state]
    return new_sessions


# ---------------------------------------------------------------------------
# Mode 3: Update Project
# ---------------------------------------------------------------------------

def match_session_to_project(working_dir: str, projects: list) -> dict | None:
    """Find the project that best matches the working directory (longest prefix)."""
    best_match = None
    best_len = 0
    
    for project in projects:
        for proj_dir in project["working_directories"]:
            if working_dir.startswith(proj_dir):
                if len(proj_dir) > best_len:
                    best_match = project
                    best_len = len(proj_dir)
    
    return best_match

def create_project_from_template(vault_path: Path, project_name: str, working_dir: str, date: str) -> Path:
    """Create a new project note from template."""
    projects_dir = vault_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-name from path
    path_parts = [p for p in working_dir.split("/") if p and p not in ("", "Users", "home")]
    if len(path_parts) >= 2:
        auto_name = path_parts[-1]
    elif path_parts:
        auto_name = path_parts[-1]
    else:
        auto_name = project_name
    
    slug = slugify(auto_name).title().replace("-", " ")
    filename = f"{slug.replace(' ', '-')}.md"
    note_path = projects_dir / filename
    
    # Check if template exists
    template_path = vault_path / "skills" / "sync-projects" / "templates" / "Project.md"
    if template_path.exists():
        template = template_path.read_text()
    else:
        # Fallback template
        template = """---
title: "{project_name}"
type: project
status: active
date_start: {date}
date_end: {date}
tags: [project]
working_directories:
  - {working_dir}
session_count: 0
---

## Overview
_Describe what this project is and what was worked on._

## Working Directories
{dir_status}

## What Was Accomplished
_Key achievements across all conversations._

## Notable Decisions
_Key technical or design decisions._

<!-- AUTO-CONVERSATIONS-START -->
## Conversation Timeline
| Date | Summary | Source | Dir |
|------|---------|--------|-----|
<!-- AUTO-CONVERSATIONS-END -->
"""
    
    dir_exists = "✅" if os.path.exists(working_dir) else "❌"
    dir_status = f"- `{working_dir}` — {dir_exists} {'exists' if os.path.exists(working_dir) else 'not found'}"
    
    content = template.format(
        project_name=slug,
        date=date,
        working_dir=working_dir,
        dir_status=dir_status,
    )
    
    note_path.write_text(content)
    return note_path

def update_project_note(vault_path: Path, project_note_path: Path, session_id: str, working_dir: str, title: str, date: str, source: str, summary: str):
    """Update an existing project note with a new session."""
    content = project_note_path.read_text()
    
    # Find the AUTO-CONVERSATIONS block
    start_marker = "<!-- AUTO-CONVERSATIONS-START -->"
    end_marker = "<!-- AUTO-CONVERSATIONS-END -->"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print(f"Warning: Could not find conversation markers in {project_note_path.name}", file=sys.stderr)
        return
    
    # Extract existing table
    before = content[:start_idx + len(start_marker)]
    after = content[end_idx:]
    
    existing_section = content[start_idx + len(start_marker):end_idx]
    
    # Check directory exists
    dir_exists = "✅" if os.path.exists(working_dir) else "❌"
    
    # Build new row
    new_row = f"| {date} | {summary} | {source} | {dir_exists} |"
    
    # Append to table
    lines = existing_section.strip().split("\n")
    if len(lines) <= 2:
        # Only header, no data yet
        table = f"""
## Conversation Timeline
| Date | Summary | Source | Dir |
|------|---------|--------|-----|
{new_row}
"""
    else:
        # Append to existing data
        table = existing_section.rstrip() + "\n" + new_row + "\n"
    
    # Rebuild content
    new_content = before + table + after
    
    # Update frontmatter dates and session count
    frontmatter = parse_frontmatter(new_content)
    
    # Update date_end if this session is newer
    current_end = frontmatter.get("date_end", "")
    if not current_end or date > current_end:
        new_content = re.sub(
            r"date_end: .*",
            f"date_end: {date}",
            new_content,
        )
    
    # Increment session_count
    current_count = frontmatter.get("session_count", 0)
    if isinstance(current_count, str):
        try:
            current_count = int(current_count)
        except:
            current_count = 0
    new_count = current_count + 1
    new_content = re.sub(
        r"session_count: \d+",
        f"session_count: {new_count}",
        new_content,
    )
    
    project_note_path.write_text(new_content)

def update_project(vault_path: Path, session_id: str, working_dir: str, title: str, date: str, source: str, summary: str):
    """Update a project note with a new session (creates project if needed)."""
    projects = list_projects(vault_path)
    
    # Match session to project
    matched_project = match_session_to_project(working_dir, projects)
    
    if matched_project:
        # Update existing project
        project_note_path = vault_path / matched_project["note_path"]
        update_project_note(vault_path, project_note_path, session_id, working_dir, title, date, source, summary)
    else:
        # Create new project
        project_note_path = create_project_from_template(vault_path, title, working_dir, date)
        update_project_note(vault_path, project_note_path, session_id, working_dir, title, date, source, summary)
    
    # Mark session as processed
    state_file = vault_path / "projects" / ".processed_sessions.json"
    state = load_state(vault_path)
    state[session_id] = datetime.now().isoformat()
    
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Helper script for sync-projects skill")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault")
    parser.add_argument("--list-projects", action="store_true", help="List existing projects")
    parser.add_argument("--list-new", action="store_true", help="List unprocessed sessions")
    parser.add_argument("--update", metavar="SESSION_ID", help="Update a project with a session")
    parser.add_argument("--working-dir", help="Working directory (for --update)")
    parser.add_argument("--title", help="Conversation title (for --update)")
    parser.add_argument("--date", help="Date YYYY-MM-DD (for --update)")
    parser.add_argument("--source", help="Source e.g. 'Cortex (ahuck)' (for --update)")
    parser.add_argument("--summary", help="1-3 sentence summary (for --update)")
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault).expanduser().resolve()
    if not vault_path.exists():
        print(json.dumps({"error": f"Vault path does not exist: {vault_path}"}), file=sys.stderr)
        sys.exit(1)
    
    if args.list_projects:
        projects = list_projects(vault_path)
        print(json.dumps(projects, indent=2))
    
    elif args.list_new:
        sessions = list_new_sessions(vault_path)
        print(json.dumps(sessions, indent=2))
    
    elif args.update:
        if not all([args.working_dir, args.title, args.date, args.source, args.summary]):
            print(json.dumps({"error": "--update requires: --working-dir, --title, --date, --source, --summary"}), file=sys.stderr)
            sys.exit(1)
        
        update_project(
            vault_path,
            args.update,
            args.working_dir,
            args.title,
            args.date,
            args.source,
            args.summary,
        )
        print(json.dumps({"status": "updated", "session_id": args.update}))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
