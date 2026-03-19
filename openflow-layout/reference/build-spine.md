# Build Spine

The spine is the main happy path through a flow — the sequence of processors from source to final destination, following success relationships.

## Why Not `find_flow_spine()`

`nipyapi.layout.find_flow_spine(pg_id)` returns the longest path by connection count, which may go through retry loops instead of the happy path. Build the spine manually instead.

## Algorithm

Walk forward from the source node, always preferring success relationships. Stop when you hit a cycle or a non-processor destination.

```python
SUCCESS_RELS = {'success', 'Original', 'Response'}

def build_spine(start_id, adjacency, processor_ids):
    spine = [start_id]
    visited = {start_id}
    current = start_id
    while current in adjacency:
        edges = adjacency[current]
        proc_edges = [e for e in edges if e['dst'] in processor_ids]
        if not proc_edges:
            break
        success_edges = [e for e in proc_edges if any(r in SUCCESS_RELS for r in e['rels'])]
        chosen = success_edges[0] if success_edges else proc_edges[0]
        if chosen['dst'] in visited:
            break
        visited.add(chosen['dst'])
        spine.append(chosen['dst'])
        current = chosen['dst']
    return spine
```

## Output

An ordered list of processor IDs forming the main vertical path. The first element is the source, the last is the deepest processor on the happy path.

Build a rank lookup for later phases:

```python
spine_rank = {pid: rank for rank, pid in enumerate(spine)}
```
