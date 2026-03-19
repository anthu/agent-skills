# Constants & Coordinate Helpers

## Component Dimensions

| Component | Width (px) | Height (px) |
|-----------|-----------|-------------|
| Processor | 352 | 128 |
| Process Group | 384 | 176 |
| Funnel | 48 | 48 |
| Input/Output Port | 240 | 80 |
| Label | variable | variable |
| Queue Box | 224 | 56 |

## Layout Constants

| Constant | Value | Derivation |
|----------|-------|------------|
| GRID_SIZE | 8 | NiFi snap grid |
| ORIGIN_Y | 80 | First row top edge |
| GOLDEN_RATIO | 1.618… | φ |
| PROCESSOR_HEIGHT | 128 | |
| BLOCK_HEIGHT | 208 | 128 + snap(128/φ) = 128 + 80 |
| MULTI_FLOW_GAP | 216 | snap(352/φ) |
| X_BETWEEN_COMPONENTS | 110 | NiFi same-row horizontal gap |
| X_BETWEEN_COMPONENT_AND_LABEL | 10 | Min gap: component edge → label |
| SHALLOW_GRAPH_DEPTH | 3 | Max downstream depth for same-row placement |

## Default Column Centers

| Column | Center X | Typical value |
|--------|----------|---------------|
| Left channel | `spine_center - 672` | 24 |
| Spine | agent-provided | 696 |
| Right channel | same as spine | 696 |

`spine_center` and `left_center` are NOT constants — the agent provides them at runtime.

## Helper Functions

```python
GRID_SIZE = 8
ORIGIN_Y = 80
PROCESSOR_HEIGHT = 128
BLOCK_HEIGHT = 208

def snap(val):
    return round(val / GRID_SIZE) * GRID_SIZE

def center_x(col_center, width):
    return snap(col_center - width / 2)

def center_y(row_center, height):
    return snap(row_center - height / 2)

def row_center_y(rank):
    return ORIGIN_Y + rank * BLOCK_HEIGHT + PROCESSOR_HEIGHT // 2

DIMS = {
    'processor': (352, 128),
    'process_group': (384, 176),
    'funnel': (48, 48),
    'port': (240, 80),
    'label': (200, 24),
}

SAME_ROW_RELATIONSHIPS = frozenset({
    'failure', 'unmatched', 'matched', 'not found',
    'timeout', 'retry', 'invalid', 'duplicate',
})
SHALLOW_GRAPH_DEPTH = 3
```

## Center-Alignment Principle

Each column is defined by its **center X**, not a left edge. A component's top-left position:

```
x = snap(column_center - width / 2)
y = snap(row_center - height / 2)
```

A processor (352px) and a process group (384px) in the same column have different X positions but share the same visual center. Same for Y — taller components sit slightly higher to stay vertically centered.
