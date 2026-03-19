# Algorithm Reference Index

The Row-Grid layout algorithm is documented across individual reference files. This file serves as an index.

## Reference Files

| Phase | File | Purpose |
|-------|------|---------|
| Setup | `constants.md` | Dimensions, grid, coordinate helpers |
| 1 | `fetch-and-classify.md` | Fetch flow, build adjacency, detect independent flows |
| 2 | `build-spine.md` | Spine detection (prefer success relationships) |
| 3 | `layout-spine.md` | Place spine components vertically |
| 4a | `layout-retry-loops.md` | Left-channel: retry, PGs, failed terminals |
| 4b | `layout-branches.md` | Fan-out placement for forks |
| 4c | `layout-terminals.md` | Success/failed terminal placement |
| 4d | `layout-labels.md` | Label positioning |
| 5 | `bounding-box-and-overlaps.md` | Bbox calculation, overlap detection & resolution |
| 6 | `multi-flow.md` | Side-by-side independent flow layout |
| 7 | `apply-and-verify.md` | Move components, screenshot verification |
| — | `worked-example.md` | KuCoin AllTickers v2 end-to-end walkthrough |

## Calculator Script

`scripts/layout_calculator.py` — Pure Python coordinate math (no nipyapi dependency). Key functions:

| Function | Purpose |
|----------|---------|
| `compute_layout()` | Compute all positions for a single flow |
| `layout_multi_flow()` | Place multiple flows side by side |
| `flow_bounding_box()` | Bounding box from BBox list |
| `flow_bounding_box_from_positions()` | Bounding box from positions + component types |
| `check_overlaps()` | Pairwise overlap detection |
| `estimate_queue_boxes()` | Approximate queue box positions |

## API Reference

### Safe Move Functions (work on running flows)

| Function | Use for |
|----------|---------|
| `layout.move_component(comp, (x, y))` | Any component (auto-detects type) |
| `layout.move_processor(proc, (x, y))` | Processors |
| `layout.move_funnel(funnel, (x, y))` | Funnels |
| `layout.move_label(label, (x, y))` | Labels |
| `layout.move_process_group(pg, (x, y))` | Process groups |
| `layout.move_port(port, (x, y))` | Input/output ports |

### Analysis Functions

| Function | Returns |
|----------|---------|
| `layout.find_flow_spine(pg_id)` | Ordered spine components (use build-spine.md instead) |
| `layout.get_side_branches(pg_id, spine)` | Branch points → components |
| `layout.get_canvas_bounds(pg_id)` | Bounding box dict |
| `layout.suggest_flow_layout(pg_id)` | Layout plan dict |
| `layout.get_position(comp)` | Current `(x, y)` tuple |
