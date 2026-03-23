---
name: streamlit-multipage-nav
description: "Builds reliable multi-page Streamlit apps using st.navigation and st.Page. Use when: building multi-page apps, fixing navigation issues, shared components across pages, sidebar layout, dynamic navigation menus, role-based page access, pages not loading via URL, import errors in page files, shared state across pages. CRITICAL: page files must go in views/ directory, NEVER pages/ (legacy auto-discovery conflict). Triggers: multi-page, multipage, st.navigation, st.Page, pages directory, shared sidebar, common layout, page not found, navigation menu, dynamic pages, role-based navigation, streamlit pages."
---

# Multi-Page Streamlit Apps with st.navigation

This skill teaches you how to build robust multi-page Streamlit apps that work correctly regardless of which page URL a user enters. The key problems it solves:

1. **Pages break when accessed directly via URL** (not through the homepage)
2. **Shared components (sidebar, header, auth) fail to load on non-default pages**
3. **Import errors** when page files try to use shared utilities
4. **Session state is empty** when a user arrives at a deep link

## Mental Model

The entrypoint file (`app.py` or `streamlit_app.py`) is **not** a page — it is a **router and frame**. It runs on EVERY page load, regardless of which URL the user visits. This is the single most important concept:

```
User visits /settings
    → Streamlit runs app.py (entrypoint)
        → app.py calls st.navigation() which returns the "settings" page
        → app.py renders shared elements (sidebar, logo, auth check)
        → app.py calls pg.run() which executes views/settings.py
```

Because the entrypoint always runs first, you place ALL shared setup there: authentication gates, sidebar widgets, logos, database connections, and session state initialization.

## Mandatory Steps

Before writing any code, load these references based on what you need:

1. **Always load first**: [reference/architecture.md](reference/architecture.md) — canonical project structure and the entrypoint template. This is non-negotiable.
2. **If shared utilities are needed**: [reference/shared-components.md](reference/shared-components.md) — how to create a `shared/` package that pages can reliably import.
3. **For advanced patterns**: [reference/patterns.md](reference/patterns.md) — auth gating, role-based nav, hidden pages, dynamic menus, custom navigation UI.

## Core Rules

These rules prevent the most common failures. They exist because agents repeatedly get them wrong.

### Rule 1: The entrypoint is the router, not a page

The file passed to `streamlit run` must:
- Call `st.navigation()` exactly once
- Call `pg.run()` exactly once
- Place shared UI elements (sidebar, logo, title) BETWEEN `st.navigation()` and `pg.run()`
- NEVER contain page-specific content

```python
# app.py — the entrypoint
import streamlit as st

# 1. Define pages (use views/, NEVER pages/)
pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/settings.py", title="Settings", icon=":material/settings:"),
]

# 2. Create navigation (returns selected page)
pg = st.navigation(pages)

# 3. Shared elements go here — they appear on EVERY page
st.set_page_config(page_title="My App", page_icon=":material/apps:", layout="wide")
st.logo("assets/logo.png")
st.sidebar.title("My App")

# 4. Run the selected page
pg.run()
```

### Rule 2: ALL pages must be declared in st.navigation on every run

If a user navigates to `/settings` via URL, Streamlit starts a fresh session and runs the entrypoint. If `st.navigation()` does not include the settings page during that run, the user sees "Page not found."

This means conditional page lists must handle the initial state correctly:

```python
# WRONG — first run with empty session_state hides all pages
if st.session_state.get("logged_in"):
    pg = st.navigation([home, dashboard, settings])
else:
    pg = st.navigation([login_page])
# User visiting /dashboard via URL → "Page not found"

# RIGHT — include all URL-accessible pages, or gate at the page level
# Option A: Always include pages, check auth inside each page
# Option B: Use visibility="hidden" for pages that should be URL-accessible but not in the menu
```

### Rule 3: NEVER name the page directory `pages/` — use `views/` instead

The directory name `pages/` is reserved by Streamlit's legacy auto-discovery system. When `.py` files exist in `pages/`, Streamlit may detect them for legacy multi-page mode, which conflicts with `st.navigation()`. On Streamlit in Snowflake (SiS), this causes the entrypoint to crash on rerun and fall back to auto-discovery — running pages independently without session state initialization.

```
your-app/
├── app.py              # Entrypoint (router + frame)
├── views/              # Page files (NOT pages/ — that name conflicts!)
│   ├── home.py
│   ├── dashboard.py
│   └── settings.py
├── shared/             # Shared utilities (Python package)
│   ├── __init__.py
│   └── components.py
└── assets/             # Static files
    └── logo.png
```

Streamlit adds the entrypoint's parent directory to `sys.path`, so `from shared.components import sidebar_filters` works from any page file.

### Rule 4: Initialize session state in the entrypoint, before pg.run()

Session state initialization belongs in the entrypoint so it happens on every run, before any page code executes:

```python
# app.py
if "user" not in st.session_state:
    st.session_state.user = None
if "theme" not in st.session_state:
    st.session_state.theme = "light"

pg = st.navigation(pages)
# ... shared elements ...
pg.run()
```

Pages can then safely read `st.session_state.user` without KeyError.

### Rule 5: Shared sidebar content goes in the entrypoint

Anything that should appear on every page — sidebar navigation aids, user info, filters — belongs in the entrypoint between `st.navigation()` and `pg.run()`:

```python
pg = st.navigation(pages)

with st.sidebar:
    st.image("assets/logo.png", width=200)
    if st.session_state.user:
        st.write(f"Logged in as {st.session_state.user}")

pg.run()
```

Page-specific sidebar content goes inside the page file itself.

## Quick-Start Template

For a basic multi-page app with shared sidebar:

```python
# app.py
import streamlit as st

home = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)
data = st.Page("views/data.py", title="Data", icon=":material/table_chart:")
about = st.Page("views/about.py", title="About", icon=":material/info:")

pg = st.navigation([home, data, about])
st.set_page_config(page_title="My App", layout="wide")
st.sidebar.title("My App")
pg.run()
```

```python
# views/home.py
import streamlit as st

st.title("Welcome")
st.write("This is the home page.")
```

Each page file is a standalone script. It does NOT call `st.navigation()` or `st.set_page_config()` (unless overriding the entrypoint's config).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Page not found" on direct URL access | Page not in `st.navigation()` during initial run | Ensure all URL-accessible pages are always passed to `st.navigation()` |
| Shared sidebar missing on some pages | Sidebar code is in a page file, not the entrypoint | Move shared sidebar code to entrypoint, between `st.navigation()` and `pg.run()` |
| `ImportError` when page imports shared module | Missing `__init__.py` in shared package | Add `__init__.py` to the `shared/` directory |
| `KeyError` on session state in page | State not initialized before page runs | Initialize all session state keys in the entrypoint before `pg.run()` |
| Page content appears twice | `pg.run()` called more than once or page code in entrypoint | Ensure `pg.run()` is called exactly once; entrypoint has no page content |
| Navigation menu not updating | Page list is static | Rebuild page list dynamically before calling `st.navigation()` each rerun |
| Sidebar reverts to showing auto-discovered page names (lowercase, no icons) | Page files in `pages/` directory conflict with legacy auto-discovery | Rename directory to `views/` — `pages/` is reserved by Streamlit's legacy system |
| `AttributeError: st.session_state has no attribute "X"` | Entrypoint crashed on rerun; pages run without state init | Check for `pages/` directory conflict (see Rule 3); ensure all state uses `.get()` as fallback |
