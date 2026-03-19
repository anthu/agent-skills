# Layout Labels

Position labels relative to their associated components. Read `reference/constants.md` first for helper functions.

## Label Types and Positions

| Label type | Anchor component | Position formula |
|------------|------------------|------------------|
| Flow title | First spine node | `(snap(spine_x - 56), snap(spine_y - 80))` |
| DDL / retry-path | Intermediate PG | `(snap(pg_x + PG_WIDTH + 100), snap(ref_y + 56))` |
| Success annotation | Success funnel | `(snap(funnel_x - 24), snap(funnel_y + FUNNEL_SIZE + 8))` |
| Failed annotation | Failed funnel | `(snap(funnel_x - 32), snap(funnel_y + FUNNEL_SIZE + 8))` |

## Placement Code

```python
PG_WIDTH = 384
FUNNEL_SIZE = 48

for label in labels:
    label_entity = label_map[label.id]
    ltype = classify_label(label)

    if ltype == 'title':
        sx, sy = positions[spine[0]]
        positions[label.id] = (snap(sx - 56), snap(sy - 80))

    elif ltype == 'ddl_path':
        pg_x, pg_y = positions[associated_pg_id]
        ref_y = center_y(row_center_y(associated_rank + 1), 128)
        positions[label.id] = (snap(pg_x + PG_WIDTH + 100), snap(ref_y + 56))

    elif ltype == 'success_annotation':
        fx, fy = positions[associated_funnel_id]
        positions[label.id] = (snap(fx - 24), snap(fy + FUNNEL_SIZE + 8))

    elif ltype == 'failed_annotation':
        fx, fy = positions[associated_funnel_id]
        positions[label.id] = (snap(fx - 32), snap(fy + FUNNEL_SIZE + 8))
```

## Classifying Labels

NiFi labels don't have a "type" field — classify by text content or proximity:
- Contains the flow/PG name → title
- Contains "DDL" or path-like text → ddl_path
- Near a success funnel → success_annotation
- Near a failed funnel → failed_annotation
- Unknown → place below the nearest component with a 16px gap
