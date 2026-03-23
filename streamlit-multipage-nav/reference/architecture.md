# Canonical Project Architecture

This document defines the exact project structure and complete entrypoint template for multi-page Streamlit apps using `st.navigation`.

## Directory Structure

```
your-app/
├── app.py                  # Entrypoint: router + shared frame
├── views/                  # All page files (NEVER use pages/ — see below)
│   ├── home.py             # Default page (default=True)
│   ├── dashboard.py
│   ├── settings.py
│   └── admin/              # Subdirectories are fine
│       ├── users.py
│       └── config.py
├── shared/                 # Python package for shared code
│   ├── __init__.py         # REQUIRED — makes this a package
│   ├── components.py       # Reusable UI components
│   ├── auth.py             # Authentication helpers
│   ├── data.py             # Data fetching / caching
│   └── state.py            # Session state initialization
├── assets/                 # Static files (images, CSS)
│   ├── logo.png
│   └── style.css
└── .streamlit/             # Streamlit config
    └── config.toml
```

### Why this structure works

- `app.py` is at the root — Streamlit adds its parent directory to `sys.path`
- `views/` is a sibling of `app.py` — relative paths like `"views/home.py"` resolve correctly
- `shared/` is importable from everywhere because the root is on `sys.path`
- `assets/` keeps static files out of the code directories

### CRITICAL: Never use `pages/` as directory name

The directory name `pages/` is reserved by Streamlit's legacy auto-discovery multi-page system. If `.py` files exist in a `pages/` directory, Streamlit detects them for legacy mode. This conflicts with `st.navigation()` and causes the entrypoint to crash on rerun — especially on Streamlit in Snowflake (SiS). The symptom is the sidebar flipping between `st.navigation()` titles and auto-discovered lowercase filenames, followed by `AttributeError` on session state keys.

Always use `views/` (or any other name that isn't `pages/`).

## Complete Entrypoint Template

This is the canonical `app.py` structure. Every multi-page app should follow this pattern:

```python
import streamlit as st
from shared.state import init_session_state

# ─── 1. SESSION STATE INITIALIZATION ─────────────────────────────
# This runs before ANYTHING else, so all pages can rely on these keys.
init_session_state()

# ─── 2. PAGE DEFINITIONS ─────────────────────────────────────────
# Define ALL pages upfront. Every page that should be URL-accessible
# must appear here on every rerun, even if hidden from the nav menu.

home = st.Page(
    "views/home.py",
    title="Home",
    icon=":material/home:",
    default=True,
)
dashboard = st.Page(
    "views/dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
)
settings = st.Page(
    "views/settings.py",
    title="Settings",
    icon=":material/settings:",
)

# ─── 3. NAVIGATION ───────────────────────────────────────────────
# Pass pages as a list (flat menu) or dict (grouped with section headers).

pg = st.navigation([home, dashboard, settings])

# ─── 4. PAGE CONFIG ──────────────────────────────────────────────
# Call AFTER st.navigation so the page title can be dynamic if needed.
st.set_page_config(
    page_title="My App",
    page_icon=":material/apps:",
    layout="wide",
)

# ─── 5. SHARED UI FRAME ──────────────────────────────────────────
# Everything here appears on EVERY page. This is the "picture frame."

st.logo("assets/logo.png")

with st.sidebar:
    st.title("My App")
    if st.session_state.user:
        st.caption(f"Logged in as {st.session_state.user}")

# ─── 6. RUN THE SELECTED PAGE ────────────────────────────────────
pg.run()
```

### What happens at runtime

1. User visits any URL (e.g., `/dashboard`)
2. Streamlit executes `app.py` top-to-bottom
3. `init_session_state()` ensures all keys exist
4. `st.navigation()` reads the URL, matches it to a page, returns that page
5. Shared sidebar/logo/config renders
6. `pg.run()` executes `views/dashboard.py`

If the user visits a URL that doesn't match any declared page, Streamlit shows "Page not found" and redirects to the default page.

## Grouped Navigation (with section headers)

Pass a dict instead of a list to create section headers in the sidebar:

```python
pg = st.navigation({
    "Main": [home, dashboard],
    "Account": [settings, profile],
    "Admin": [users, config],
})
```

## Page File Template

Each page file is a simple script. It should NOT call `st.navigation()`.

```python
# views/dashboard.py
import streamlit as st
from shared.components import metric_card
from shared.data import load_metrics

st.title("Dashboard")

metrics = load_metrics()
cols = st.columns(3)
for i, (label, value) in enumerate(metrics.items()):
    with cols[i]:
        metric_card(label, value)
```

Key rules for page files:
- No `st.navigation()` calls
- No `st.set_page_config()` unless intentionally overriding the entrypoint's config
- Import shared utilities from `shared.*`
- Can use `st.sidebar` for page-specific sidebar content (it appends to the entrypoint's sidebar)
- Can use `st.session_state` freely — keys were initialized in the entrypoint

## Session State Initialization Module

```python
# shared/state.py
import streamlit as st

def init_session_state():
    defaults = {
        "user": None,
        "role": None,
        "theme": "light",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
```

This pattern prevents KeyError on any page, regardless of entry point.

## st.Page API Reference

```python
st.Page(
    page,           # str path, Path object, or callable (no args)
    title=None,     # Label in nav menu + browser tab title
    icon=None,      # Emoji or :material/icon_name:
    url_path=None,  # Custom URL path (no slashes allowed)
    default=False,  # True = this is the homepage (url_path ignored)
    visibility="visible",  # "visible" or "hidden"
)
```

- `page`: Relative path from entrypoint, or a callable
- `default=True`: Page serves at root URL `/`. Only one page should be default.
- `visibility="hidden"`: Page is accessible via URL and `st.switch_page()` but not shown in nav menu
- `url_path`: Custom URL segment. Defaults to inferred from filename.

## st.navigation API Reference

```python
pg = st.navigation(
    pages,          # list[StreamlitPage] or dict[str, list[StreamlitPage]]
    position="sidebar",  # "sidebar", "hidden"
)
```

- Returns the `StreamlitPage` matching the current URL
- Must be called exactly once per rerun, in the entrypoint file only
- `position="hidden"`: Suppresses the default nav widget (build your own with `st.page_link`)
