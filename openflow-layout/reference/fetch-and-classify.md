# Fetch & Classify

## Fetch Flow Contents

```python
import nipyapi

pg = nipyapi.canvas.get_process_group("<name or id>")
flow = nipyapi.canvas.get_flow(pg.id)

processors = flow.process_group_flow.flow.processors
connections = flow.process_group_flow.flow.connections
funnels = flow.process_group_flow.flow.funnels
labels = flow.process_group_flow.flow.labels
process_groups = flow.process_group_flow.flow.process_groups
input_ports = flow.process_group_flow.flow.input_ports
output_ports = flow.process_group_flow.flow.output_ports
```

## Build Adjacency Map

```python
adjacency = {}
reverse_adj = {}
for conn in connections:
    src = conn.component.source.id
    dst = conn.component.destination.id
    rels = conn.component.selected_relationships or []
    adjacency.setdefault(src, []).append({'dst': dst, 'rels': rels, 'conn': conn})
    reverse_adj.setdefault(dst, []).append({'src': src, 'rels': rels, 'conn': conn})

all_ids = {p.id for p in processors}
all_ids |= {f.id for f in funnels}
all_ids |= {pg.id for pg in process_groups}
all_ids |= {p.id for p in input_ports}
all_ids |= {p.id for p in output_ports}
```

## Identify Structural Elements

| Element | Detection |
|---------|-----------|
| Source nodes | IDs in `all_ids` with no entries in `reverse_adj` |
| Sink nodes | IDs in `all_ids` with no entries in `adjacency` |
| Processor IDs | `{p.id for p in processors}` |

## Detect Independent Flows

Use BFS from each source node to find connected components:

```python
def find_independent_flows(all_ids, adjacency, reverse_adj):
    visited = set()
    flows = []
    for start in sorted(all_ids):
        if start in visited:
            continue
        if start in reverse_adj:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in component:
                continue
            component.add(node)
            for edge in adjacency.get(node, []):
                queue.append(edge['dst'])
            for edge in reverse_adj.get(node, []):
                queue.append(edge['src'])
        visited |= component
        flows.append(component)
    return flows
```

## Classification Output

After this phase you should have:
- `adjacency` and `reverse_adj` maps
- `source_nodes`: list of entry points (no incoming connections)
- `sink_nodes`: list of terminal components (no outgoing connections)
- `flows`: list of sets, each containing the component IDs of one independent flow
- Count of independent flows → determines single-flow vs multi-flow path
