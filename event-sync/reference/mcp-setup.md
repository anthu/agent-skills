# MCP Server Setup Guide

This skill requires two MCP servers. Follow the instructions below to install and configure them.

## 1. Google Workspace MCP Server

**Status:** Bundled with Cortex Code — no manual installation needed.

The Google Workspace server is managed by Cortex Code and auto-configured. On first use it will prompt you to authenticate with your Google account via OAuth.

**Verification:**
```
# In Cortex Code, run:
$event-sync
# The skill will check if google-workspace tools are available
```

If it does not appear, ensure your Cortex Code installation is up to date:
```bash
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

## 2. mcp-ical (Apple Calendar MCP Server)

**Status:** Community package — requires manual installation.

### Install

```bash
# Clone the repository
git clone https://github.com/matthewdeanmartin/mcp-ical.git ~/.local/share/mcp-ical

# Install dependencies
cd ~/.local/share/mcp-ical
uv sync
```

### Configure

Add the following to `~/.snowflake/cortex/mcp.json`. Create the file if it doesn't exist, or add the `mcp-ical` entry to the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "mcp-ical": {
      "type": "stdio",
      "command": "<PATH_TO_UV>",
      "args": [
        "--directory",
        "<HOME>/.local/share/mcp-ical",
        "run",
        "mcp-ical"
      ]
    }
  }
}
```

Replace:
- `<PATH_TO_UV>` with the output of `which uv` (e.g. `/Users/you/.local/bin/uv`)
- `<HOME>` with your home directory (e.g. `/Users/you`)

### Verify

Restart Cortex Code, then check the server responds:
```
# In a Cortex Code session, ask:
"List my calendars using the iCal MCP server"
```

You should see a list of your Apple Calendar calendars.

### macOS Permissions

On first use, macOS will prompt you to grant Calendar access to the terminal/Cortex Code process. You must approve this for the server to work.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `google-workspace` tools not found | Update Cortex Code CLI, restart session |
| `mcp-ical` tools not found | Check `mcp.json` path and `uv` binary path |
| Calendar access denied | System Settings → Privacy & Security → Calendars → enable for Terminal/Cortex |
| `uv` not found | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
