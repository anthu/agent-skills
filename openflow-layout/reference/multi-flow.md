# Multi-Flow Layout

Handle process groups containing multiple independent flows. Each flow is laid out separately, then placed side by side.

## Detect Independent Flows

After running `reference/fetch-and-classify.md`, you have a list of flows (connected components). If `len(flows) > 1`, use this reference.

## Per-Flow Layout

For each independent flow, follow the single-flow process:

1. Read `reference/build-spine.md` → detect spine from that flow's source node
2. Read `reference/layout-spine.md` → place spine
3. Classify edges within this flow:
   - Back-edges → `reference/layout-retry-loops.md`
   - Fan-outs → `reference/layout-branches.md`
   - Terminals → `reference/layout-terminals.md`
   - Labels → `reference/layout-labels.md`

Compute each flow at the default `spine_center=696` — the positions will be shifted in the next step.

## Side-by-Side Placement

Use the calculator's `layout_multi_flow()` to arrange flows with proper bounding-box spacing:

```python
exec(open('scripts/layout_calculator.py').read())

flow_configs = []
for flow_data in per_flow_results:
    flow_configs.append({
        'spine_center': 696,
        'left_center': flow_data.get('left_center', 24),
        'spine': flow_data['spine'],
        'retry_loops': flow_data.get('retry_loops', []),
        'success_terminals': flow_data.get('success_terminals', []),
        'labels': flow_data.get('labels', []),
    })

all_positions, all_boxes = layout_multi_flow(flow_configs, gap=216)
```

## How It Works

Two-pass approach:

1. **Pass 1:** Compute each flow's layout at origin (`spine_center=696`) to get actual bounding boxes
2. **Pass 2:** Shift each flow horizontally so `flow[N].left = flow[N-1].right + gap`

The gap defaults to `MULTI_FLOW_GAP` (216px, derived from golden ratio: `snap(352/φ)`).

All flows share the same `ORIGIN_Y` so their top rows align horizontally.

## After Placement

Read `reference/bounding-box-and-overlaps.md` to validate no cross-flow overlaps exist, then proceed to `reference/apply-and-verify.md`.
