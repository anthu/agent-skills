# Layout Branches (Fan-Outs)

Handle spine nodes with multiple outgoing edges to non-spine destinations. Read `reference/constants.md` first for helper functions.

## Detecting Branches

A branch exists when a spine node has ≥2 outgoing connections where at least one destination is not the next spine node.

```python
for rank, proc_id in enumerate(spine):
    edges = adjacency.get(proc_id, [])
    non_spine_targets = [e for e in edges if e['dst'] not in spine_rank]
    if len(non_spine_targets) >= 1 and len(edges) >= 2:
        # This is a fork point
        pass
```

## Placement: 2-Way Fork

For a spine node with one success path (stays on spine) and one branch (e.g., failure):

```python
branch_w, branch_h = DIMS.get(branch_type, (352, 128))
branch_x = center_x(spine_center + 400, branch_w)
branch_y = center_y(row_center_y(source_rank + 1), branch_h)
positions[branch_id] = (branch_x, branch_y)
```

The branch child goes one row below and one column to the right of the spine.

## Placement: N-Way Fan-Out (N ≥ 3)

Spread children horizontally, centered under the parent:

```python
N = len(children)
horizontal_spread = (N - 1) * BLOCK_HEIGHT

for i, child_id in enumerate(sorted_children):
    child_w, child_h = DIMS.get(child_type, (352, 128))
    child_x = snap(spine_center - horizontal_spread / 2 + i * BLOCK_HEIGHT - child_w / 2)
    child_y = center_y(row_center_y(source_rank + 1), child_h)
    positions[child_id] = (child_x, child_y)
```

## Sub-Spines

If a branch child has its own successors, continue laying out vertically below it (like a mini-spine):

```python
sub_rank = 0
current = branch_child_id
while current in adjacency:
    sub_rank += 1
    next_edges = [e for e in adjacency[current] if e['dst'] not in positions]
    if not next_edges:
        break
    next_id = next_edges[0]['dst']
    w, h = DIMS.get(type_of(next_id), (352, 128))
    positions[next_id] = (positions[current][0], center_y(row_center_y(source_rank + 1 + sub_rank), h))
    current = next_id
```
