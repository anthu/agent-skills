# Bounding Box & Overlap Resolution

Calculate bounding boxes, detect overlaps, and resolve them. Uses `scripts/layout_calculator.py` for the math.

## Load the Calculator

```python
import os
script_dir = os.path.dirname(os.path.abspath(__file__))  # or use skill path
exec(open(os.path.join(script_dir, 'scripts/layout_calculator.py')).read())
```

## Calculate Bounding Box

A bounding box encloses all components of a laid-out flow:

```python
def flow_bounding_box(positions, component_dims):
    min_x = min(x for x, y in positions.values())
    min_y = min(y for x, y in positions.values())
    max_x = max(x + component_dims[cid][0] for cid, (x, y) in positions.items())
    max_y = max(y + component_dims[cid][1] for cid, (x, y) in positions.items())
    return {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y,
            'width': max_x - min_x, 'height': max_y - min_y}
```

The calculator's `flow_bounding_box(positions, boxes)` returns a `BBox` object with `.x`, `.y`, `.w`, `.h`.

## Check Overlaps

Pairwise comparison of all component bounding boxes with padding:

```python
positions, boxes = compute_layout(
    spine_center=696,
    spine=spine_list,
    retry_loops=loops,
    success_terminals=terminals,
    labels=label_list,
    left_center=24,
)

overlaps = check_overlaps(boxes, padding=16)
if overlaps:
    for a, b in overlaps:
        print(f'  OVERLAP: {a} <-> {b}')
```

## Estimate Queue Box Positions

Queue info boxes (224×56) appear centered on connection midpoints. Check these for overlaps too:

```python
conn_list = [(src_id, dst_id, label) for each connection]
queue_boxes = estimate_queue_boxes(conn_list, positions)
all_overlaps = check_overlaps(boxes + queue_boxes, padding=16)
```

## Resolving Overlaps

### Same Column — Insert Empty Row

If two components in the same column overlap vertically, push everything below the conflict down by `BLOCK_HEIGHT`:

```python
conflict_y = max(a.y, b.y)
for cid, (x, y) in positions.items():
    if y >= conflict_y:
        positions[cid] = (x, y + BLOCK_HEIGHT)
```

### Queue Box Overlap — Nudge Horizontally

If queue boxes overlap, nudge one component horizontally by `QUEUE_BOX_WIDTH + 16`:

```python
positions[affected_id] = (x + QUEUE_BOX_WIDTH + 16, y)
```

### Cross-Column Overlap — Widen Column Gap

If left-channel and spine components overlap, shift the entire left channel further left:

```python
left_center -= 200
for cid in left_channel_ids:
    w = component_dims[cid][0]
    positions[cid] = (center_x(left_center, w), positions[cid][1])
```

### Flow-to-Flow Overlap — Shift Entire Flow

If two independently-laid-out flows overlap, shift the rightward flow:

```python
bbox1 = flow_bounding_box(flow1_positions, flow1_boxes)
bbox2 = flow_bounding_box(flow2_positions, flow2_boxes)
if bbox1.overlaps(bbox2, pad=MULTI_FLOW_GAP):
    dx = snap(bbox1.right_edge() + MULTI_FLOW_GAP - bbox2.x)
    for cid in flow2_positions:
        x, y = flow2_positions[cid]
        flow2_positions[cid] = (x + dx, y)
```

## Iterative Resolution

After any adjustment, re-run `check_overlaps` to verify. Repeat until zero overlaps remain (typically 1-2 iterations).
