"""
Layout validation hooks for openflow-layout skill.

Requires nipyapi. Use as a context manager around any block that moves
components to assert that only positions (and optionally bends) changed:

    import nipyapi
    import nipyapi.layout as layout
    from scripts.layout_validator import LayoutValidator

    with LayoutValidator(pg_id) as v:
        for comp_id, (x, y) in positions.items():
            layout.move_component(comp_map[comp_id], (snap(x), snap(y)))
    # Raises AssertionError if anything other than positions changed.

When intentionally setting self-loop bendpoints, pass strip_bends=True so
those changes are excluded from the comparison:

    with LayoutValidator(pg_id, strip_bends=True):
        for comp_id, (x, y) in positions.items():
            layout.move_component(comp_map[comp_id], (snap(x), snap(y)))
        conn.component.bends = bendpoints
        nipyapi.nifi.ConnectionsApi().update_connection(conn.id, conn)
"""

import nipyapi


def _strip_positions(obj, strip_bends=False):
    skip = {'position'}
    if strip_bends:
        skip.add('bends')
    if isinstance(obj, dict):
        return {k: _strip_positions(v, strip_bends) for k, v in obj.items()
                if k not in skip}
    if isinstance(obj, list):
        return [_strip_positions(i, strip_bends) for i in obj]
    return obj


def _find_diffs(a, b, path=''):
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            child = f'{path}.{k}' if path else k
            if k not in a:
                diffs.append((child, '<missing>', b[k]))
            elif k not in b:
                diffs.append((child, a[k], '<missing>'))
            else:
                diffs.extend(_find_diffs(a[k], b[k], child))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append((path, f'len={len(a)}', f'len={len(b)}'))
        else:
            for i, (ai, bi) in enumerate(zip(a, b)):
                diffs.extend(_find_diffs(ai, bi, f'{path}[{i}]'))
    elif a != b:
        diffs.append((path, a, b))
    return diffs


def flow_logic_snapshot(pg_id, strip_bends=False):
    """Fetch the flow and return a dict with all position fields removed."""
    flow = nipyapi.canvas.get_flow(pg_id)
    return _strip_positions(flow.to_dict(), strip_bends=strip_bends)


class LayoutValidator:
    """
    Context manager that asserts only positions (and optionally bends) changed.

    Args:
        pg_id: NiFi process group ID to monitor.
        strip_bends: If True, connection bendpoints are excluded from the
                     comparison (use when intentionally setting bendpoints).
    """

    def __init__(self, pg_id, strip_bends=False):
        self.pg_id = pg_id
        self.strip_bends = strip_bends
        self._before = None

    def __enter__(self):
        self._before = flow_logic_snapshot(self.pg_id, strip_bends=self.strip_bends)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        after = flow_logic_snapshot(self.pg_id, strip_bends=self.strip_bends)
        diffs = _find_diffs(self._before, after)
        if diffs:
            preview = '\n'.join(
                f'  {path}: {old!r} -> {new!r}' for path, old, new in diffs[:10]
            )
            suffix = f'\n  ... and {len(diffs) - 10} more' if len(diffs) > 10 else ''
            raise AssertionError(
                f'Non-position changes detected ({len(diffs)} diff(s)):\n{preview}{suffix}'
            )
        return False
