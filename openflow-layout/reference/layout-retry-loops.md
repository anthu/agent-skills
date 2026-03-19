# Layout Retry Loops

Place retry/error-recovery components in the left channel. Read `reference/constants.md` first for helper functions.

## Detecting Retry Loops

A retry loop exists when a connection goes from spine node S to a processor that eventually connects back to an earlier spine node T. The pattern:

```
Spine node S (failure source) → Retry processor → [Intermediate PG] → Spine node T (feedback target)
```

Detect back-edges: connections where the destination is on the spine AND has a lower rank than the source.

```python
back_edges = []
for src_id in adjacency:
    if src_id not in spine_rank:
        continue
    for edge in adjacency[src_id]:
        dst = edge['dst']
        if dst not in spine_rank:
            for sub_edge in adjacency.get(edge['dst'], []):
                if sub_edge['dst'] in spine_rank and spine_rank[sub_edge['dst']] <= spine_rank[src_id]:
                    back_edges.append({
                        'source_rank': spine_rank[src_id],
                        'target_rank': spine_rank[sub_edge['dst']],
                        'retry_id': edge['dst'],
                        'intermediates': [],  # fill in PGs on the path
                    })
```

## Visual Pattern

```
Row T-1:  [PG (left)]         [Spine T-1]
Row T:                         [T / feedback target]
  ...
Row S:                         [S / failure source]
Row S+1:  [Retry (left)]
Row S+2:  [✗ Failed (left)]
```

## Placement Formulas

All left-channel components are center-aligned on `left_center`:

```python
retry_w, retry_h = DIMS[retry_type]
retry_x = center_x(left_center, retry_w)
retry_y = center_y(row_center_y(S_rank + 1), retry_h)
positions[retry_id] = (retry_x, retry_y)
```

**Intermediate PG** (e.g., DDL process group feeding back into spine):

```python
pg_w, pg_h = DIMS['process_group']
pg_x = center_x(left_center, pg_w)
pg_y = center_y(row_center_y(T_rank - 1), pg_h)
positions[pg_id] = (pg_x, pg_y)
```

**Failed terminal** (funnel below retry processor):

```python
f_w, f_h = DIMS['funnel']
f_x = center_x(left_center, f_w)
f_y = center_y(row_center_y(S_rank + 2), f_h)
positions[failed_id] = (f_x, f_y)
```

## Multiple Retry Loops

If a flow has more than one retry loop, shift `left_center` further left for each additional loop to prevent overlap:

```python
loop_left_center = left_center - (loop_index * 400)
```
