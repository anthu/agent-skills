# Layout Spine

Place spine components vertically, center-aligned on the spine column. Read `reference/constants.md` first for helper functions.

## Placement

Each spine node gets a row rank (0, 1, 2, ...). Position using center-alignment:

```python
positions = {}

for rank, proc_id in enumerate(spine):
    w, h = DIMS.get(comp_type(proc_id), (352, 128))
    x = center_x(spine_center, w)
    y = center_y(row_center_y(rank), h)
    positions[proc_id] = (x, y)
```

## Row Spacing

Rows are spaced by `BLOCK_HEIGHT` (208px), derived from the golden ratio:

```
Row 0 center Y: 80 + 0×208 + 64 = 144
Row 1 center Y: 80 + 1×208 + 64 = 352
Row 2 center Y: 80 + 2×208 + 64 = 560
```

A processor (128px tall) at row 0: `y = center_y(144, 128) = 80`
A process group (176px tall) at row 0: `y = center_y(144, 176) = 56`

## Tracking Occupied Rows

Track which rows are occupied by spine nodes — this prevents later phases from placing terminals in the same row:

```python
spine_rows = set(range(len(spine)))
```

## Output

`positions` dict mapping processor IDs to `(x, y)` tuples. Pass this forward to subsequent layout phases.
