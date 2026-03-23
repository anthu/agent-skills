# Advanced Patterns

Common patterns for multi-page Streamlit apps using `st.navigation`.

## Pattern 1: Authentication Gating

The challenge: when a logged-out user visits `/dashboard` via URL, the app must not crash — it should redirect to login.

```python
# app.py
import streamlit as st
from shared.state import init_session_state

init_session_state()

def login_page():
    st.header("Log in")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        if authenticate(username, password):  # your auth logic
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout_page():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

login = st.Page(login_page, title="Log in", icon=":material/login:")
logout = st.Page(logout_page, title="Log out", icon=":material/logout:")

home = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)
dashboard = st.Page("views/dashboard.py", title="Dashboard", icon=":material/dashboard:")
settings = st.Page("views/settings.py", title="Settings", icon=":material/settings:")

if st.session_state.get("logged_in"):
    pg = st.navigation({
        "Account": [logout],
        "Main": [home, dashboard, settings],
    })
else:
    pg = st.navigation([login])

st.set_page_config(page_title="My App")
pg.run()
```

**How this handles deep links:**
- User visits `/dashboard` while logged out → `st.session_state.logged_in` is falsy → only `login` page is in navigation → Streamlit doesn't recognize `/dashboard` → redirects to default (login)
- User visits `/dashboard` while logged in → all pages are declared → dashboard loads normally

This is the correct pattern. The key insight: when the user is not logged in, pages like `/dashboard` SHOULD be inaccessible, so omitting them from `st.navigation()` is the right behavior.

## Pattern 2: Role-Based Navigation

Different users see different pages based on their role:

```python
# app.py
all_pages = {
    "viewer": [home, reports],
    "editor": [home, reports, editor],
    "admin":  [home, reports, editor, admin_panel, user_mgmt],
}

role = st.session_state.get("role", "viewer")
pages = all_pages.get(role, [home])

pg = st.navigation(pages)
pg.run()
```

For grouped menus with role-based sections:

```python
page_dict = {}
page_dict["Main"] = [home]

if role in ["editor", "admin"]:
    page_dict["Content"] = [editor, drafts]
if role == "admin":
    page_dict["Admin"] = [admin_panel, user_mgmt]

page_dict["Account"] = [settings, logout]

pg = st.navigation(page_dict)
```

## Pattern 3: Hidden Pages (URL-accessible but not in menu)

Use `visibility="hidden"` for pages that should be reachable via URL or `st.switch_page()` but not cluttering the navigation menu:

```python
detail_page = st.Page(
    "views/item_detail.py",
    title="Item Detail",
    url_path="item",
    visibility="hidden",
)

# Include it in navigation so it's accessible
pg = st.navigation([home, catalog, detail_page])
```

From the catalog page, link to the detail page:

```python
# views/catalog.py
import streamlit as st

for item in items:
    if st.button(item["name"], key=item["id"]):
        st.session_state.selected_item = item["id"]
        st.switch_page("views/item_detail.py")
```

The detail page reads the item from session state:

```python
# views/item_detail.py
import streamlit as st

if "selected_item" not in st.session_state:
    st.warning("No item selected.")
    st.switch_page("views/catalog.py")
    st.stop()

item_id = st.session_state.selected_item
st.title(f"Item {item_id}")
```

## Pattern 4: Custom Navigation UI

Hide the default navigation and build your own with `st.page_link`:

```python
# app.py
pg = st.navigation(pages, position="hidden")

with st.sidebar:
    st.page_link("views/home.py", label="Home", icon=":material/home:")
    st.page_link("views/dashboard.py", label="Dashboard", icon=":material/dashboard:")
    st.divider()
    st.page_link("views/settings.py", label="Settings", icon=":material/settings:")

pg.run()
```

This gives full control over spacing, dividers, grouping, and conditional display.

## Pattern 5: Dynamic Page List from Config

Build pages dynamically from a config dict or database:

```python
PAGE_CONFIG = [
    {"file": "views/home.py", "title": "Home", "icon": ":material/home:", "default": True},
    {"file": "views/sales.py", "title": "Sales", "icon": ":material/attach_money:"},
    {"file": "views/inventory.py", "title": "Inventory", "icon": ":material/inventory:"},
]

pages = [
    st.Page(
        p["file"],
        title=p["title"],
        icon=p.get("icon"),
        default=p.get("default", False),
    )
    for p in PAGE_CONFIG
]

pg = st.navigation(pages)
```

## Pattern 6: Pages Defined as Callables

Pages can be Python functions instead of files. Useful for simple pages or pages generated dynamically:

```python
def about_page():
    st.title("About")
    st.write("Version 1.0")

def contact_page():
    st.title("Contact")
    st.write("email@example.com")

pg = st.navigation([
    st.Page("views/home.py", title="Home", default=True),
    st.Page(about_page, title="About", icon=":material/info:"),
    st.Page(contact_page, title="Contact", icon=":material/mail:"),
])
pg.run()
```

Callable pages cannot accept arguments. Pass data through `st.session_state`.

## Pattern 7: Programmatic Page Switching

Use `st.switch_page()` to navigate programmatically (e.g., after form submission):

```python
# views/create_item.py
import streamlit as st

with st.form("create"):
    name = st.text_input("Name")
    if st.form_submit_button("Create"):
        save_item(name)
        st.switch_page("views/catalog.py")
```

`st.switch_page()` accepts the same path string used in `st.Page()`.

## Anti-Patterns to Avoid

### 1. Calling st.navigation in a page file

```python
# views/dashboard.py
st.navigation([...])  # WRONG — only the entrypoint calls st.navigation
```

### 2. Putting page content in the entrypoint

```python
# app.py
pg = st.navigation(pages)
st.title("Dashboard")  # WRONG if this is page-specific content
st.dataframe(df)        # This shows on EVERY page
pg.run()
```

Only shared elements go in the entrypoint.

### 3. Initializing session state inside page files

```python
# views/dashboard.py
if "data" not in st.session_state:  # FRAGILE — may not run if another page loads first
    st.session_state.data = load_data()
```

Initialize in the entrypoint or in `shared/state.py`, called from the entrypoint.

### 4. Hardcoding page paths with leading slashes

```python
st.Page("/views/home.py", ...)   # WRONG — use relative paths
st.Page("views/home.py", ...)    # RIGHT
```

### 5. Multiple default pages

```python
home = st.Page("views/home.py", default=True)
dash = st.Page("views/dash.py", default=True)  # WRONG — only one default allowed
```
