---
name: streamlit-multipage-nav
description: "Builds reliable multi-page Streamlit apps using st.navigation and st.Page. Use when: building multi-page apps, fixing navigation issues, shared components across pages, sidebar layout, dynamic navigation menus, role-based page access, pages not loading via URL, import errors in page files, shared state across pages. CRITICAL: page files must go in views/ directory, NEVER pages/ (legacy auto-discovery conflict). Triggers: multi-page, multipage, st.navigation, st.Page, pages directory, shared sidebar, common layout, page not found, navigation menu, dynamic pages, role-based navigation, streamlit pages."
---

# Multi-Page Streamlit Apps with st.navigation

This skill builds robust multi-page Streamlit apps that work correctly regardless of which page URL a user enters. The key problems it solves:

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

## References

Read [reference/architecture.md](reference/architecture.md) first — it has the canonical project structure, entrypoint template, and API reference. Then load as needed:

- [reference/shared-components.md](reference/shared-components.md) — creating a `shared/` package for imports across pages
- [reference/patterns.md](reference/patterns.md) — auth gating, role-based nav, hidden pages, dynamic menus, custom navigation UI

## Core Rules

These rules prevent the most common failures. They exist because agents repeatedly get them wrong.

### Rule 1: The entrypoint is the router, not a page

The file passed to `streamlit run` must call `st.navigation()` exactly once and `pg.run()` exactly once. Shared UI elements (sidebar, logo, title) go BETWEEN those two calls. The entrypoint must never contain page-specific content. See `reference/architecture.md` for the full canonical template.

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

### Rule 3: Use `views/` for page files, NEVER `pages/`

The name `pages/` triggers Streamlit's legacy auto-discovery system, which conflicts with `st.navigation()`. On Streamlit in Snowflake (SiS), this causes the entrypoint to crash on rerun and fall back to running pages independently without session state. Use `views/` or any other name that isn't `pages/`.

### Rule 4: Initialize session state in the entrypoint, before pg.run()

Session state initialization belongs in the entrypoint so it runs before any page code executes — on every rerun, regardless of which URL the user entered. Pages can then safely read state keys without `KeyError`. See the `init_session_state()` pattern in `reference/architecture.md`.

### Rule 5: Shared sidebar content goes in the entrypoint

Anything that should appear on every page — sidebar nav aids, user info, logos — belongs in the entrypoint between `st.navigation()` and `pg.run()`. Page-specific sidebar content goes inside the page file itself (it appends below the entrypoint's sidebar content).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Page not found" on direct URL access | Page not in `st.navigation()` during initial run | Ensure all URL-accessible pages are always passed to `st.navigation()` |
| Shared sidebar missing on some pages | Sidebar code is in a page file, not the entrypoint | Move shared sidebar code to entrypoint, between `st.navigation()` and `pg.run()` |
| `ImportError` when page imports shared module | Missing `__init__.py` in shared package | Add `__init__.py` to the `shared/` directory |
| `KeyError` on session state in page | State not initialized before page runs | Initialize all session state keys in the entrypoint before `pg.run()` |
| Page content appears twice | `pg.run()` called more than once or page code in entrypoint | Ensure `pg.run()` is called exactly once; entrypoint has no page content |
| Navigation menu not updating | Page list is static | Rebuild page list dynamically before calling `st.navigation()` each rerun |
| Sidebar reverts to auto-discovered page names | Page files in `pages/` directory | Rename directory to `views/` (Rule 3) |
| `AttributeError: st.session_state has no attribute "X"` | Entrypoint crashed on rerun; pages run without state init | Check for `pages/` directory conflict (Rule 3); use `.get()` as fallback |
