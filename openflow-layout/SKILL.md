---
name: openflow-layout
description: "Autonomously lays out NiFi/Openflow flows on the canvas using a Row-Grid algorithm. Classifies edges (spine, retry loops, forks, terminals), positions components on a center-aligned row grid with retry loops on the left and success terminals on the right. Supports multiple flows side by side. Use for ANY request to layout, organize, tidy, arrange, position, clean up, or visually fix a NiFi flow or process group. Triggers: layout, organize, tidy, arrange, position, clean up flow, messy flow, overlapping processors, fix canvas, rearrange."
---

# Openflow Layout

You are an expert NiFi user arranging flows so every processor, connection, and label is perfectly visible and logically organized. You use a **Row-Grid** algorithm — see the `reference/` directory for each phase.

## Safety Rules

**You MUST follow these rules absolutely:**

1. **ONLY change coordinates.** Reposition processors, funnels, ports, labels, and process groups.
2. **NEVER stop, start, enable, disable, or delete any component.**
3. **NEVER modify processor configuration, properties, or relationships.**
4. **NEVER create or remove connections.**
5. **ONLY use `nipyapi.layout.move_*` functions to reposition components.** Direct API calls send the full entity including config, which NiFi rejects with 409 Conflict if the processor is running.
6. **NEVER use `ConnectionsApi().update_connection()` or `canvas.update_connection()` on running flows.** NiFi returns 409 for ANY connection entity update when the destination processor is running.

If unsure whether an API call modifies something beyond coordinates, do not make it.

## Session Prerequisites

1. Load `references/core-guidelines.md` and `references/core-session.md` from the openflow skill
2. Follow the Session Start Workflow (cache check, profile selection)
3. Only proceed once a profile is confirmed

```python
import nipyapi
nipyapi.profiles.switch('<profile>')
```

## Orchestration Checklist

Work autonomously through these steps. Do not ask the user what to do at each step — just do it.

### Step 1: Load Constants

Read `reference/constants.md` — dimensions, grid helpers, coordinate formulas.

### Step 2: Fetch & Classify

Read `reference/fetch-and-classify.md` — fetch the flow, build adjacency maps, detect independent flows.

### Step 3: Route by Flow Count

| Flows found | Action |
|-------------|--------|
| **1 flow** | Continue to Step 4 |
| **>1 flows** | Read `reference/multi-flow.md` — it orchestrates per-flow layout internally, then skip to Step 5 |
| **PG grid request** | Use `layout.align_pg_grid(root_id, sort_by_name=True, columns=4)` — no further steps needed |

### Step 4: Single-Flow Layout

Execute these sub-steps in order. Read only the references that apply to this flow's structure:

| Sub-step | Reference | When to read |
|----------|-----------|--------------|
| 4a. Detect spine | `reference/build-spine.md` | Always |
| 4b. Place spine | `reference/layout-spine.md` | Always |
| 4c. Place retry loops | `reference/layout-retry-loops.md` | If back-edges exist (connections looping to earlier spine nodes) |
| 4d. Place branches | `reference/layout-branches.md` | If any spine node has ≥2 outgoing edges to non-spine destinations |
| 4e. Place terminals | `reference/layout-terminals.md` | If funnels, output ports, or dead-end processors exist |
| 4f. Place labels | `reference/layout-labels.md` | If labels exist in the flow |

### Step 5: Validate & Resolve Overlaps

Read `reference/bounding-box-and-overlaps.md` — calculate bounding boxes, check for overlaps (including queue boxes), and resolve any conflicts.

### Step 6: Apply & Verify

Read `reference/apply-and-verify.md` — move components using `nipyapi.layout.move_*`, ask user for screenshot, make nudge adjustments if needed.

## Quick Reference

**Worked example:** See `reference/worked-example.md` for a complete KuCoin AllTickers v2 walkthrough.

**Component dimensions:**

| Component | Width | Height |
|-----------|-------|--------|
| Processor | 352 | 128 |
| Process Group | 384 | 176 |
| Funnel | 48 | 48 |
| Port | 240 | 80 |
| Queue Box | 224 | 56 |

**Spatial metaphor:** right = success, left = error/retry, down = forward flow.

## Known Limitations

- **Connection bends** cannot be modified on running flows (409 Conflict). Position components for natural routing instead.
- **Large fan-outs (5+)** may need manual width tuning.
- **Very large flows (30+)** — consider breaking into sub-process-groups first.
