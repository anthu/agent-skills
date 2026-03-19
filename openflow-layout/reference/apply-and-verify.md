# Apply & Verify

Move components to computed positions and validate the result. This is the final phase — run after all positions are computed and overlaps resolved.

## Build Component Map

Re-fetch the flow to get current entities (stale objects cause 409 errors):

```python
import nipyapi
import nipyapi.layout as layout

flow = nipyapi.canvas.get_flow(pg_id)
comp_map = {}
for p in flow.process_group_flow.flow.processors:
    comp_map[p.id] = p
for f in flow.process_group_flow.flow.funnels:
    comp_map[f.id] = f
for pg in flow.process_group_flow.flow.process_groups:
    comp_map[pg.id] = pg
for lbl in flow.process_group_flow.flow.labels:
    comp_map[lbl.id] = lbl
for port in flow.process_group_flow.flow.input_ports:
    comp_map[port.id] = port
for port in flow.process_group_flow.flow.output_ports:
    comp_map[port.id] = port
```

## Apply Positions

Use ONLY `nipyapi.layout.move_*` functions — direct API calls fail on running processors (409 Conflict).

```python
def snap(val):
    return round(val / 8) * 8

for comp_id, (x, y) in positions.items():
    comp = comp_map.get(comp_id)
    if comp:
        layout.move_component(comp, (snap(x), snap(y)))
```

## Refresh After Moves

After moving components, the original objects have stale coordinates. If you need to do relative positioning after the batch move, re-fetch:

```python
flow = nipyapi.canvas.get_flow(pg_id)
```

## Screenshot Verification

Ask the user for visual confirmation:

> "I've laid out the flow. Could you take a screenshot so I can verify it looks correct?"

Review the screenshot for:
- Overlapping processors or labels
- Connections crossing through components
- Queue boxes overlapping each other
- Components off-screen or too far apart

## Self-Loop Connections

When a processor connects back to itself, place two bend points to the right of the component so the connection arcs cleanly without overlapping the body:

```python
bendpoints = compute_self_loop_bendpoints(
    component_id=cid,
    positions=positions,
    component_types={'cid': 'processor'},
)
# Returns: [(loop_x, cy - 25), (loop_x, cy + 25)]
# where loop_x = snap(x + w + w/2 + 5)
```

Apply bendpoints via nipyapi after moving the component:

```python
conn = nipyapi.canvas.get_connection(connection_id)
conn.component.bends = [{'x': bx, 'y': by} for bx, by in bendpoints]
nipyapi.nifi.ConnectionsApi().update_connection(conn.id, conn)
```

## Nudge Adjustments

If issues are found, make targeted fixes:

```python
comp = comp_map[problem_id]
current_x, current_y = layout.get_position(comp)
layout.move_component(comp, (snap(current_x + offset_x), snap(current_y + offset_y)))
```

Then ask for another screenshot to confirm.
