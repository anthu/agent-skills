#!/usr/bin/env python3
"""
DCM Schema Discovery Script

Discovers all objects in a Snowflake schema and generates DCM-compatible definitions.

Usage:
    python discover_schema.py --connection <conn> --database <db> --schema <schema> --output <dir>

Output:
    - discovery_report.json: Full inventory with categorization
    - definitions/: DEFINE statements for supported objects
    - hooks/: POST_HOOK statements for external stages, streams, etc.
    - unsupported/: Grants and objects requiring manual handling
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_sql(connection: str, sql: str) -> str:
    """Execute SQL via snow sql and return output."""
    cmd = ["snow", "sql", "-c", connection, "-q", sql, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SQL Error: {result.stderr}", file=sys.stderr)
        return "[]"
    return result.stdout


def run_sql_text(connection: str, sql: str) -> str:
    """Execute SQL via snow sql and return text output."""
    cmd = ["snow", "sql", "-c", connection, "-q", sql]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SQL Error: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout


def parse_json_output(output: str) -> list:
    """Parse JSON output from snow sql."""
    try:
        if not output.strip():
            return []
        data = json.loads(output)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def discover_tables(connection: str, database: str, schema: str) -> list:
    """Discover all tables in the schema."""
    sql = f"SHOW TABLES IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "kind": r.get("kind", "TABLE")} for r in rows]


def discover_views(connection: str, database: str, schema: str) -> list:
    """Discover all views in the schema."""
    sql = f"SHOW VIEWS IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "is_secure": r.get("is_secure") == "true"} for r in rows]


def discover_dynamic_tables(connection: str, database: str, schema: str) -> list:
    """Discover all dynamic tables in the schema."""
    sql = f"SHOW DYNAMIC TABLES IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "warehouse": r.get("warehouse")} for r in rows]


def discover_stages(connection: str, database: str, schema: str) -> list:
    """Discover all stages in the schema, categorizing internal vs external."""
    sql = f"SHOW STAGES IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    
    stages = []
    for r in rows:
        name = r.get("name")
        url = r.get("url", "")
        is_external = bool(url and url.strip())
        stages.append({
            "name": name,
            "url": url,
            "is_external": is_external,
            "type": r.get("type", "")
        })
    return stages


def discover_tasks(connection: str, database: str, schema: str) -> list:
    """Discover all tasks in the schema."""
    sql = f"SHOW TASKS IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "schedule": r.get("schedule")} for r in rows]


def discover_streams(connection: str, database: str, schema: str) -> list:
    """Discover all streams in the schema."""
    sql = f"SHOW STREAMS IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "source_type": r.get("source_type")} for r in rows]


def discover_functions(connection: str, database: str, schema: str) -> list:
    """Discover all user-defined functions in the schema."""
    sql = f"SHOW USER FUNCTIONS IN SCHEMA {database}.{schema}"
    output = run_sql(connection, sql)
    rows = parse_json_output(output)
    return [{"name": r.get("name"), "arguments": r.get("arguments")} for r in rows]


def get_ddl(connection: str, object_type: str, fqn: str) -> str:
    """Get DDL for a specific object."""
    sql = f"SELECT GET_DDL('{object_type}', '{fqn}')"
    output = run_sql_text(connection, sql)
    lines = output.strip().split('\n')
    if len(lines) > 2:
        return '\n'.join(lines[2:]).strip()
    return ""


def convert_to_define(ddl: str) -> str:
    """Convert CREATE DDL to DEFINE statement."""
    result = re.sub(r'^CREATE\s+OR\s+REPLACE\s+', 'DEFINE ', ddl, flags=re.IGNORECASE | re.MULTILINE)
    result = re.sub(r'^CREATE\s+', 'DEFINE ', result, flags=re.IGNORECASE | re.MULTILINE)
    result = re.sub(r'\s+IF\s+NOT\s+EXISTS', '', result, flags=re.IGNORECASE)
    return result


def write_file(path: Path, content: str):
    """Write content to file, creating directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Discover Snowflake schema objects for DCM import")
    parser.add_argument("--connection", "-c", required=True, help="Snowflake connection name")
    parser.add_argument("--database", "-d", required=True, help="Database name")
    parser.add_argument("--schema", "-s", required=True, help="Schema name")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--include-grants", action="store_true", help="Include grant discovery")
    parser.add_argument("--object-types", help="Comma-separated object types to discover (default: all)")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    definitions_dir = output_dir / "definitions"
    hooks_dir = output_dir / "hooks"
    unsupported_dir = output_dir / "unsupported"
    
    print(f"=== DCM Schema Discovery ===")
    print(f"Connection: {args.connection}")
    print(f"Source: {args.database}.{args.schema}")
    print(f"Output: {args.output}")
    print()
    
    discovery = {
        "metadata": {
            "connection": args.connection,
            "database": args.database,
            "schema": args.schema,
            "discovered_at": datetime.now().isoformat(),
        },
        "objects": {
            "tables": [],
            "views": [],
            "dynamic_tables": [],
            "stages_internal": [],
            "stages_external": [],
            "tasks": [],
            "streams": [],
            "functions": [],
        },
        "summary": {
            "defineable": 0,
            "post_hook": 0,
            "unsupported": 0,
        }
    }
    
    tables_sql = []
    views_sql = []
    dynamic_tables_sql = []
    stages_sql = []
    tasks_sql = []
    hooks_sql = []
    
    print("Discovering tables...")
    tables = discover_tables(args.connection, args.database, args.schema)
    for t in tables:
        fqn = f"{args.database}.{args.schema}.{t['name']}"
        ddl = get_ddl(args.connection, "TABLE", fqn)
        if ddl:
            define_stmt = convert_to_define(ddl)
            tables_sql.append(define_stmt + ";\n")
            discovery["objects"]["tables"].append({"name": t["name"], "fqn": fqn})
    print(f"  Found {len(tables)} tables")
    
    print("Discovering views...")
    views = discover_views(args.connection, args.database, args.schema)
    for v in views:
        fqn = f"{args.database}.{args.schema}.{v['name']}"
        ddl = get_ddl(args.connection, "VIEW", fqn)
        if ddl:
            define_stmt = convert_to_define(ddl)
            views_sql.append(define_stmt + ";\n")
            discovery["objects"]["views"].append({"name": v["name"], "fqn": fqn, "is_secure": v.get("is_secure", False)})
    print(f"  Found {len(views)} views")
    
    print("Discovering dynamic tables...")
    dts = discover_dynamic_tables(args.connection, args.database, args.schema)
    for dt in dts:
        fqn = f"{args.database}.{args.schema}.{dt['name']}"
        ddl = get_ddl(args.connection, "DYNAMIC_TABLE", fqn)
        if ddl:
            define_stmt = convert_to_define(ddl)
            dynamic_tables_sql.append(define_stmt + ";\n")
            discovery["objects"]["dynamic_tables"].append({"name": dt["name"], "fqn": fqn})
    print(f"  Found {len(dts)} dynamic tables")
    
    print("Discovering stages...")
    stages = discover_stages(args.connection, args.database, args.schema)
    for s in stages:
        fqn = f"{args.database}.{args.schema}.{s['name']}"
        ddl = get_ddl(args.connection, "STAGE", fqn)
        if ddl:
            if s["is_external"]:
                hook_stmt = f"CREATE STAGE IF NOT EXISTS {fqn}\n    URL = '{s['url']}';\n"
                hooks_sql.append(hook_stmt)
                discovery["objects"]["stages_external"].append({"name": s["name"], "fqn": fqn, "url": s["url"]})
            else:
                define_stmt = convert_to_define(ddl)
                stages_sql.append(define_stmt + ";\n")
                discovery["objects"]["stages_internal"].append({"name": s["name"], "fqn": fqn})
    print(f"  Found {len([s for s in stages if not s['is_external']])} internal stages")
    print(f"  Found {len([s for s in stages if s['is_external']])} external stages (POST_HOOK)")
    
    print("Discovering tasks...")
    tasks = discover_tasks(args.connection, args.database, args.schema)
    for t in tasks:
        fqn = f"{args.database}.{args.schema}.{t['name']}"
        ddl = get_ddl(args.connection, "TASK", fqn)
        if ddl:
            define_stmt = convert_to_define(ddl)
            tasks_sql.append(define_stmt + ";\n")
            discovery["objects"]["tasks"].append({"name": t["name"], "fqn": fqn})
    print(f"  Found {len(tasks)} tasks")
    
    print("Discovering streams...")
    streams = discover_streams(args.connection, args.database, args.schema)
    for s in streams:
        fqn = f"{args.database}.{args.schema}.{s['name']}"
        ddl = get_ddl(args.connection, "STREAM", fqn)
        if ddl:
            hooks_sql.append(f"-- Stream: {s['name']}\n{ddl};\n")
            discovery["objects"]["streams"].append({"name": s["name"], "fqn": fqn})
    print(f"  Found {len(streams)} streams (POST_HOOK)")
    
    discovery["summary"]["defineable"] = (
        len(discovery["objects"]["tables"]) +
        len(discovery["objects"]["views"]) +
        len(discovery["objects"]["dynamic_tables"]) +
        len(discovery["objects"]["stages_internal"]) +
        len(discovery["objects"]["tasks"])
    )
    discovery["summary"]["post_hook"] = (
        len(discovery["objects"]["stages_external"]) +
        len(discovery["objects"]["streams"])
    )
    
    print("\nWriting output files...")
    
    write_file(output_dir / "discovery_report.json", json.dumps(discovery, indent=2))
    
    if tables_sql:
        write_file(definitions_dir / "tables.sql", "-- Tables\n\n" + "\n".join(tables_sql))
    if views_sql:
        write_file(definitions_dir / "views.sql", "-- Views\n\n" + "\n".join(views_sql))
    if dynamic_tables_sql:
        write_file(definitions_dir / "dynamic_tables.sql", "-- Dynamic Tables\n\n" + "\n".join(dynamic_tables_sql))
    if stages_sql:
        write_file(definitions_dir / "stages.sql", "-- Internal Stages\n\n" + "\n".join(stages_sql))
    if tasks_sql:
        write_file(definitions_dir / "tasks.sql", "-- Tasks\n\n" + "\n".join(tasks_sql))
    
    if hooks_sql:
        hooks_content = "-- Objects requiring POST_HOOK (external stages, streams, etc.)\n\n"
        hooks_content += "ATTACH POST_HOOK AS [\n"
        hooks_content += "\n".join(["    " + line for sql in hooks_sql for line in sql.split('\n') if line.strip()])
        hooks_content += "\n];\n"
        write_file(hooks_dir / "post_hooks.sql", hooks_content)
    
    print()
    print("=== Discovery Complete ===")
    print(f"✅ DEFINE-able objects: {discovery['summary']['defineable']}")
    print(f"⚠️  POST_HOOK objects: {discovery['summary']['post_hook']}")
    print(f"\nOutput written to: {output_dir}")
    print("\nNext steps:")
    print("1. Review discovery_report.json")
    print("2. Copy definitions/* to your DCM project's sources/definitions/")
    print("3. Copy hooks/* content into your definition files")
    print("4. Run 'snow dcm raw-analyze' to validate")
    print("5. Run 'snow dcm plan' - adopted objects should show ZERO changes")


if __name__ == "__main__":
    main()
