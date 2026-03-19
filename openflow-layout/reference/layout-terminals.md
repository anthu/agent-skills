# Layout Terminals

Place success and failed terminal components (funnels, output ports, dead-end processors). Read `reference/constants.md` first for helper functions.

## Success Terminals

Success terminals are center-aligned with the spine column, one row below their source processor:

```python
tw, th = DIMS.get(terminal_type, (48, 48))
tx = center_x(spine_center, tw)
ty = center_y(row_center_y(source_rank + 1), th)
positions[terminal_id] = (tx, ty)
```

**Row conflict:** If a spine node already occupies the target row, shift the terminal right:

```python
target_row = source_rank + 1
if target_row in spine_rows:
    tx = center_x(spine_center + 300, tw)
positions[terminal_id] = (tx, ty)
```

## Failed Terminals

Failed terminals belong in the left channel, below the retry processor (handled in `layout-retry-loops.md`). If there's no retry loop and you have a standalone failure funnel:

```python
fw, fh = DIMS['funnel']
fx = center_x(left_center, fw)
fy = center_y(row_center_y(source_rank + 1), fh)
positions[failed_id] = (fx, fy)
```

## Dead-End Processors

Processors with no outgoing connections stay on the spine at their assigned rank — no special handling needed. They were already placed by `layout-spine.md`.

## Output Port Terminals

Output ports follow the same rules as funnels but use port dimensions:

```python
pw, ph = DIMS['port']  # 240 × 80
px = center_x(spine_center, pw)
py = center_y(row_center_y(source_rank + 1), ph)
positions[port_id] = (px, py)
```

## Same-Row Terminal Heuristic

Terminals whose relationship names suggest error-handling can be placed on the **same row** as their source, to the right, when the downstream subgraph is shallow (depth ≤ `SHALLOW_GRAPH_DEPTH = 3`).

```python
if is_same_row_terminal(rel_names=['failure'], downstream_depth=1):
    tx = center_x(spine_center + X_BETWEEN_COMPONENTS + PROCESSOR_WIDTH, tw)
    ty = center_y(row_center_y(source_rank), th)
    positions[terminal_id] = (tx, ty)
```

`is_same_row_terminal(rel_names, downstream_depth=0)` returns `True` when any relationship name matches `SAME_ROW_RELATIONSHIPS` (`failure`, `unmatched`, `matched`, `not found`, `timeout`, `retry`, `invalid`, `duplicate`) **and** `downstream_depth ≤ SHALLOW_GRAPH_DEPTH`.
