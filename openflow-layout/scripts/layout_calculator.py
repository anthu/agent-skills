#!/usr/bin/env python3
"""
Row-Grid layout calculator for openflow-layout skill.

Computes component positions using center-aligned columns and checks for
bounding-box overlaps.  No nipyapi dependency -- pure coordinate math.

Center-alignment: each column is defined by its CENTER X.  A component's
left-edge X = snap(column_center - width / 2).  Same for Y within a row:
top-edge Y = snap(row_center - height / 2).

Multi-flow: when a process group contains several independent flows,
compute each flow's bounding box, then place them side by side on the
same ORIGIN_Y with a configurable gap.

Usage (inline by the agent):

    exec(open('scripts/layout_calculator.py').read())

    positions, boxes = compute_layout(
        spine_center=696,
        spine=[('id1', 'processor'), ('id2', 'processor'), ('id3', 'processor')],
        retry_loops=[{
            'source_rank': 2,
            'target_rank': 2,
            'retry': ('r_id', 'processor'),
            'intermediates': [('pg_id', 'process_group')],
            'failed_terminal': ('f_id', 'funnel'),
        }],
        success_terminals=[{'source_rank': 2, 'terminal': ('s_id', 'funnel')}],
        labels=[{'id': 'lbl', 'type': 'title'}],
    )

    overlaps = check_overlaps(boxes)
    queue_boxes = estimate_queue_boxes([('id1','id2','Fetch->Wrap')], positions)
    all_overlaps = check_overlaps(boxes + queue_boxes)
"""

GRID_SIZE = 8
ORIGIN_Y = 80
GOLDEN_RATIO = 1.618033988749895

PROCESSOR_WIDTH = 352
PROCESSOR_HEIGHT = 128
BLOCK_HEIGHT = PROCESSOR_HEIGHT + round(PROCESSOR_HEIGHT / GOLDEN_RATIO / GRID_SIZE) * GRID_SIZE  # 208
PG_WIDTH = 384
PG_HEIGHT = 176
FUNNEL_SIZE = 48
LABEL_HEIGHT = 24
QUEUE_BOX_WIDTH = 224
QUEUE_BOX_HEIGHT = 56

MULTI_FLOW_GAP = round(PROCESSOR_WIDTH / GOLDEN_RATIO / GRID_SIZE) * GRID_SIZE  # 216

X_BETWEEN_COMPONENTS = 110
X_BETWEEN_COMPONENT_AND_LABEL = 10

DIMS = {
    'processor': (PROCESSOR_WIDTH, PROCESSOR_HEIGHT),
    'process_group': (PG_WIDTH, PG_HEIGHT),
    'funnel': (FUNNEL_SIZE, FUNNEL_SIZE),
    'label': (200, LABEL_HEIGHT),
    'port': (240, 80),
}

SAME_ROW_RELATIONSHIPS = frozenset({
    'failure', 'unmatched', 'matched', 'not found',
    'timeout', 'retry', 'invalid', 'duplicate',
})
SHALLOW_GRAPH_DEPTH = 3


def snap(val):
    return round(val / GRID_SIZE) * GRID_SIZE


def center_x(col_center, width):
    return snap(col_center - width / 2)


def center_y(row_center, height):
    return snap(row_center - height / 2)


def is_same_row_terminal(rel_names, downstream_depth=0):
    if downstream_depth > SHALLOW_GRAPH_DEPTH:
        return False
    lower = {r.lower() for r in rel_names}
    return any(kw in name for name in lower for kw in SAME_ROW_RELATIONSHIPS)


def compute_self_loop_bendpoints(component_id, positions, component_types=None):
    if component_id not in positions:
        return []
    x, y = positions[component_id]
    w, h = _dims((component_types or {}).get(component_id, 'processor'))
    loop_x = snap(x + w + w / 2 + 5)
    cy = y + h / 2
    return [(loop_x, snap(cy - 25)), (loop_x, snap(cy + 25))]


class BBox:
    __slots__ = ('x', 'y', 'w', 'h', 'name')

    def __init__(self, x, y, w, h, name=''):
        self.x, self.y, self.w, self.h, self.name = x, y, w, h, name

    def overlaps(self, other, pad=0):
        return not (
            self.x + self.w + pad <= other.x
            or other.x + other.w + pad <= self.x
            or self.y + self.h + pad <= other.y
            or other.y + other.h + pad <= self.y
        )

    def right_edge(self):
        return self.x + self.w

    def bottom_edge(self):
        return self.y + self.h

    def __repr__(self):
        return f'{self.name}@({self.x},{self.y} {self.w}x{self.h})'


def _dims(ctype):
    return DIMS.get(ctype, (PROCESSOR_WIDTH, PROCESSOR_HEIGHT))


def _row_center_y(rank):
    return ORIGIN_Y + rank * BLOCK_HEIGHT + PROCESSOR_HEIGHT // 2


def compute_layout(spine_center, spine, retry_loops=None, success_terminals=None,
                   labels=None, left_center=None, origin_y=None):
    """
    Compute positions for all flow components using center-aligned columns.

    Args:
        spine_center: X center of the spine column (agent provides this).
        spine: [(id, type), ...] ordered spine components.
        retry_loops: [{
            'source_rank': int,
            'target_rank': int,
            'retry': (id, type),
            'intermediates': [(id, type), ...],
            'failed_terminal': (id, type) or None,
        }, ...]
        success_terminals: [{'source_rank': int, 'terminal': (id, type)}, ...]
        labels: [{'id': str, 'type': str, ...}, ...]
        left_center: X center for left channel.  Defaults to spine_center - 672.
        origin_y: Override for ORIGIN_Y (default 80).

    Returns:
        (positions, boxes)
        positions: {id: (x, y)}
        boxes: [BBox, ...]
    """
    oy = origin_y if origin_y is not None else ORIGIN_Y
    lc = left_center if left_center is not None else spine_center - 672

    positions = {}
    boxes = []
    spine_rows = set()

    def row_cy(rank):
        return oy + rank * BLOCK_HEIGHT + PROCESSOR_HEIGHT // 2

    pg_extra_y = 0
    for rank, (cid, ctype) in enumerate(spine):
        if rank > 0 and ctype == 'process_group':
            pg_extra_y += 25
        w, h = _dims(ctype)
        x = center_x(spine_center, w)
        y = center_y(oy + pg_extra_y + rank * BLOCK_HEIGHT + PROCESSOR_HEIGHT // 2, h)
        positions[cid] = (x, y)
        boxes.append(BBox(x, y, w, h, f'spine[{rank}]'))
        spine_rows.add(rank)

    for loop in (retry_loops or []):
        src_rank = loop['source_rank']
        tgt_rank = loop.get('target_rank', src_rank)

        rid, rtype = loop['retry']
        retry_row = src_rank + 1
        rw, rh = _dims(rtype)
        rx = center_x(lc, rw)
        ry = center_y(row_cy(retry_row), rh)
        positions[rid] = (rx, ry)
        boxes.append(BBox(rx, ry, rw, rh, 'retry'))

        for pid, ptype in loop.get('intermediates', []):
            pg_row = tgt_rank - 1
            pw, ph = _dims(ptype)
            px = center_x(lc, pw)
            py = center_y(row_cy(pg_row), ph)
            positions[pid] = (px, py)
            boxes.append(BBox(px, py, pw, ph, 'intermediate'))

        if loop.get('failed_terminal'):
            fid, ftype = loop['failed_terminal']
            failed_row = retry_row + 1
            fw, fh = _dims(ftype)
            fx = center_x(lc, fw)
            fy = center_y(row_cy(failed_row), fh)
            positions[fid] = (fx, fy)
            boxes.append(BBox(fx, fy, fw, fh, 'failed'))

    for term in (success_terminals or []):
        tid, ttype = term['terminal']
        term_row = term['source_rank'] + 1
        tw, th = _dims(ttype)
        tx = center_x(spine_center, tw)
        ty = center_y(row_cy(term_row), th)
        rx = tx if term_row not in spine_rows else center_x(spine_center + 300, tw)
        positions[tid] = (rx, ty)
        boxes.append(BBox(rx, ty, tw, th, 'success'))

    for lbl in (labels or []):
        lid = lbl['id']
        lt = lbl.get('type', 'annotation')
        lw, lh = _dims('label')
        if lt == 'title':
            first_spine = spine[0] if spine else None
            if first_spine and first_spine[0] in positions:
                sx, sy = positions[first_spine[0]]
                positions[lid] = (snap(sx - 56), snap(sy - 80))
        elif lt == 'ddl_path':
            src_rank = lbl.get('source_rank', 1)
            ref_y = center_y(row_cy(src_rank + 1), PROCESSOR_HEIGHT)
            positions[lid] = (snap(center_x(lc, PG_WIDTH) + PG_WIDTH + 100), snap(ref_y + 56))
        elif lt == 'success_annotation':
            ref = lbl.get('ref_id')
            if ref and ref in positions:
                rx, ry = positions[ref]
                positions[lid] = (snap(rx - 24), snap(ry + FUNNEL_SIZE + 8))
        elif lt == 'failed_annotation':
            ref = lbl.get('ref_id')
            if ref and ref in positions:
                rx, ry = positions[ref]
                positions[lid] = (snap(rx - 32), snap(ry + FUNNEL_SIZE + 8))

    return positions, boxes


def flow_bounding_box(positions, boxes):
    if not boxes:
        return BBox(0, 0, 0, 0, 'empty')
    min_x = min(b.x for b in boxes)
    min_y = min(b.y for b in boxes)
    max_x = max(b.x + b.w for b in boxes)
    max_y = max(b.y + b.h for b in boxes)
    return BBox(min_x, min_y, max_x - min_x, max_y - min_y, 'flow_bbox')


def flow_bounding_box_from_positions(positions, component_types):
    """
    Calculate bounding box directly from a positions dict and component type map.

    Useful when the agent computes positions manually (without compute_layout())
    and needs a bounding box for overlap checking or multi-flow placement.

    Args:
        positions: {component_id: (x, y)}
        component_types: {component_id: 'processor'|'process_group'|'funnel'|...}

    Returns:
        BBox encompassing all components.
    """
    if not positions:
        return BBox(0, 0, 0, 0, 'empty')
    bboxes = []
    for cid, (x, y) in positions.items():
        w, h = _dims(component_types.get(cid, 'processor'))
        bboxes.append(BBox(x, y, w, h, str(cid)))
    return flow_bounding_box(positions, bboxes)


def layout_multi_flow(flows, gap=None):
    """
    Lay out multiple independent flows side by side in one process group.

    Two-pass approach:
      1. Compute each flow at its original spine_center to get actual bounding boxes.
      2. Shift each flow so that bbox(N).left = bbox(N-1).right + gap.

    This ensures the gap is between *actual* bounding boxes, not theoretical
    column centers, so flows without left-channel components pack tightly.

    Args:
        flows: [{
            'spine_center': int,
            'spine': [...],
            'retry_loops': [...],
            'success_terminals': [...],
            'labels': [...],
            'left_center': int or None,
        }, ...]
        gap: px gap between flow bounding boxes. Default MULTI_FLOW_GAP.

    Returns:
        (all_positions, all_boxes) merged across all flows.
    """
    g = gap if gap is not None else MULTI_FLOW_GAP

    computed = []
    for flow in flows:
        sc = flow.get('spine_center', 696)
        lc = flow.get('left_center', None)
        pos, bxs = compute_layout(
            spine_center=sc,
            spine=flow['spine'],
            retry_loops=flow.get('retry_loops'),
            success_terminals=flow.get('success_terminals'),
            labels=flow.get('labels'),
            left_center=lc,
        )
        bbox = flow_bounding_box(pos, bxs)
        computed.append((pos, bxs, bbox))

    all_positions = {}
    all_boxes = []
    cursor_x = None

    for pos, bxs, bbox in computed:
        if cursor_x is None:
            dx = 0
            cursor_x = bbox.right_edge() + g
        else:
            dx = snap(cursor_x - bbox.x)
            cursor_x = bbox.x + dx + bbox.w + g

        if dx != 0:
            shifted_pos = {cid: (x + dx, y) for cid, (x, y) in pos.items()}
            shifted_bxs = [BBox(b.x + dx, b.y, b.w, b.h, b.name) for b in bxs]
        else:
            shifted_pos = pos
            shifted_bxs = bxs

        all_positions.update(shifted_pos)
        all_boxes.extend(shifted_bxs)

    return all_positions, all_boxes


def check_overlaps(boxes, padding=16):
    overlaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i].overlaps(boxes[j], padding):
                overlaps.append((boxes[i], boxes[j]))
    return overlaps


def estimate_queue_boxes(connections, positions):
    """
    Approximate queue-box positions (centered on connection midpoint).

    connections: [(src_id, dst_id, label), ...]
    positions:   {id: (x, y)}
    """
    qboxes = []
    for src_id, dst_id, label in connections:
        if src_id not in positions or dst_id not in positions:
            continue
        sx, sy = positions[src_id]
        dx, dy = positions[dst_id]
        sw, sh = PROCESSOR_WIDTH, PROCESSOR_HEIGHT
        dw, dh = PROCESSOR_WIDTH, PROCESSOR_HEIGHT
        cx = snap((sx + sw / 2 + dx + dw / 2) / 2 - QUEUE_BOX_WIDTH / 2)
        cy = snap((sy + sh / 2 + dy + dh / 2) / 2 - QUEUE_BOX_HEIGHT / 2)
        qboxes.append(BBox(cx, cy, QUEUE_BOX_WIDTH, QUEUE_BOX_HEIGHT, 'queue:' + label))
    return qboxes


def print_layout(positions, boxes):
    print('=== Positions ===')
    for cid, (x, y) in sorted(positions.items(), key=lambda kv: kv[1][1]):
        print(f'  {cid}: ({x}, {y})')

    overlaps = check_overlaps(boxes)
    if overlaps:
        print(f'\n=== OVERLAPS ({len(overlaps)}) ===')
        for a, b in overlaps:
            print(f'  {a} <-> {b}')
    else:
        print('\n=== No overlaps ===')


if __name__ == '__main__':
    SPINE_C = 696
    LEFT_C = 24

    positions, boxes = compute_layout(
        spine_center=SPINE_C,
        spine=[
            ('fetch', 'processor'),
            ('wrap', 'processor'),
            ('stream', 'processor'),
        ],
        retry_loops=[{
            'source_rank': 2,
            'target_rank': 2,
            'retry': ('retry', 'processor'),
            'intermediates': [('pg', 'process_group')],
            'failed_terminal': ('failed_funnel', 'funnel'),
        }],
        success_terminals=[
            {'source_rank': 2, 'terminal': ('success_funnel', 'funnel')},
        ],
        labels=[
            {'id': 'title_label', 'type': 'title'},
            {'id': 'ddl_label', 'type': 'ddl_path', 'source_rank': 1},
            {'id': 'success_label', 'type': 'success_annotation', 'ref_id': 'success_funnel'},
            {'id': 'failed_label', 'type': 'failed_annotation', 'ref_id': 'failed_funnel'},
        ],
        left_center=LEFT_C,
    )

    conns = [
        ('fetch', 'wrap', 'Fetch->Wrap'),
        ('wrap', 'stream', 'Wrap->Stream'),
        ('stream', 'retry', 'Stream->Retry'),
        ('retry', 'pg', 'Retry->PG'),
        ('pg', 'stream', 'PG->Stream'),
        ('stream', 'success_funnel', 'Stream->Success'),
        ('retry', 'failed_funnel', 'Retry->Failed'),
    ]

    qboxes = estimate_queue_boxes(conns, positions)
    all_boxes = boxes + qboxes
    print_layout(positions, all_boxes)
