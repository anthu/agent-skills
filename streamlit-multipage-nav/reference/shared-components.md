# Shared Components Guide

This document explains how to build a `shared/` Python package that any page can reliably import, regardless of which URL the user enters.

## Why imports fail (and how to fix them)

The most common agent mistake is putting shared code in a file without making it a proper Python package. When Streamlit runs `app.py`, it adds the directory containing `app.py` to `sys.path`. This means:

```
your-app/           ← This directory is added to sys.path
├── app.py
├── views/
│   └── dashboard.py
└── shared/
    ├── __init__.py  ← REQUIRED for `from shared.x import y` to work
    └── components.py
```

Without `__init__.py`, Python does not recognize `shared/` as a package and imports fail.

## Setting up the shared package

### Step 1: Create the package

```
shared/
├── __init__.py       # Can be empty, but must exist
├── components.py     # Reusable UI components
├── data.py           # Data loading and caching
├── auth.py           # Authentication helpers
└── state.py          # Session state initialization
```

### Step 2: The __init__.py file

At minimum, `__init__.py` must exist (it can be empty). For convenience, re-export commonly used items:

```python
# shared/__init__.py
from shared.components import page_header, metric_card, data_table
from shared.auth import require_auth, get_current_user
from shared.state import init_session_state
```

This lets pages use shorter imports: `from shared import page_header`

## Shared Component Patterns

### Reusable UI components

Build functions that encapsulate common UI patterns:

```python
# shared/components.py
import streamlit as st

def page_header(title, description=None):
    st.title(title)
    if description:
        st.caption(description)
    st.divider()

def metric_card(label, value, delta=None):
    st.metric(label=label, value=value, delta=delta)

def data_table(df, title=None):
    if title:
        st.subheader(title)
    st.dataframe(df, use_container_width=True)

def sidebar_filters(options):
    with st.sidebar:
        selected = {}
        for key, values in options.items():
            selected[key] = st.multiselect(key, values)
        return selected
```

### Using shared components in pages

```python
# views/dashboard.py
import streamlit as st
from shared.components import page_header, metric_card

page_header("Dashboard", "Real-time overview of key metrics")

col1, col2, col3 = st.columns(3)
with col1:
    metric_card("Revenue", "$1.2M", "+12%")
with col2:
    metric_card("Users", "8,432", "+3%")
with col3:
    metric_card("Uptime", "99.9%")
```

### Cached data loading

Shared data functions should use `@st.cache_data` or `@st.cache_resource` to avoid redundant fetches:

```python
# shared/data.py
import streamlit as st

@st.cache_data(ttl=300)
def load_metrics():
    # Expensive query or API call
    return {"Revenue": "$1.2M", "Users": "8,432", "Uptime": "99.9%"}

@st.cache_resource
def get_db_connection():
    import snowflake.connector
    import os
    return snowflake.connector.connect(
        connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME", "default")
    )
```

### Authentication helpers

```python
# shared/auth.py
import streamlit as st

def require_auth():
    if not st.session_state.get("user"):
        st.warning("Please log in to access this page.")
        st.stop()

def get_current_user():
    return st.session_state.get("user")

def has_role(required_role):
    return st.session_state.get("role") == required_role
```

Usage in a page:

```python
# views/admin.py
import streamlit as st
from shared.auth import require_auth

require_auth()
st.title("Admin Panel")
```

`st.stop()` is the key — it halts the page script without crashing the app.

## Common Import Mistakes

### Mistake 1: No __init__.py

```
shared/
    components.py    ← No __init__.py!
```

Fix: Add an empty `__init__.py` file.

### Mistake 2: Importing from the wrong level

```python
# WRONG (from inside views/dashboard.py)
from components import page_header       # Fails: components is not on sys.path
from ..shared.components import page_header  # Fails: relative imports don't work in scripts

# RIGHT
from shared.components import page_header
```

Streamlit page files are scripts, not modules in a package. They cannot use relative imports. Always use absolute imports starting from the repo root.

### Mistake 3: Circular imports

```python
# shared/components.py
from shared.data import load_metrics    # This can cause circular imports if data.py imports components

# Fix: Import inside the function that needs it
def dashboard_metrics():
    from shared.data import load_metrics
    return load_metrics()
```

### Mistake 4: Using `pages/` as directory name

```
pages/               ← BAD: triggers legacy auto-discovery, conflicts with st.navigation()
    dashboard.py
    utils.py
```

NEVER name your page directory `pages/`. Streamlit's legacy auto-discovery system scans this directory for `.py` files and registers them as pages. This conflicts with `st.navigation()` and causes the entrypoint to crash on rerun — especially on Streamlit in Snowflake (SiS). Use `views/` instead.

## Sidebar Composition

The entrypoint's sidebar content appears first, then page-specific sidebar content appends below it:

```python
# app.py (entrypoint)
with st.sidebar:
    st.title("My App")           # Always visible

pg.run()
```

```python
# views/dashboard.py
with st.sidebar:
    date_range = st.date_input("Date range")   # Only on dashboard page
```

Result: The sidebar shows "My App" title on all pages. On the dashboard page, it also shows the date range picker below the title.
