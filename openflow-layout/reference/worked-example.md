# Worked Example: KuCoin AllTickers v2

End-to-end walkthrough using the Row-Grid algorithm. Parameters: `spine_center=696`, `left_center=24`.

## Flow Structure

- **Spine:** FetchWebSocket → WrapInRecord → StreamToSnowflake (3 processors)
- **Retry loop:** StreamToSnowflake fails → RetryFlowFile → DDL PG → back to StreamToSnowflake
- **Success terminal:** StreamToSnowflake success → success funnel
- **Failed terminal:** RetryFlowFile failure → failed funnel
- **Labels:** title, DDL path, success annotation, failed annotation

## Phase 1: Spine Layout (center-aligned at X=696)

```
Rank 0: FETCH   x=center_x(696,352)=520   y=center_y(144,128)=80    → (520, 80)
Rank 1: WRAP    x=520                       y=center_y(352,128)=288   → (520, 288)
Rank 2: STREAM  x=520                       y=center_y(560,128)=496   → (520, 496)
```

## Phase 2: Left Channel (center-aligned at X=24)

Back-edge: STREAM (rank 2) → RetryFlowFile → DDL PG → STREAM (rank 2)

```
PG:     x=center_x(24,384)=-168   y=center_y(352,176)=264   → (-168, 264)   [row 1]
RETRY:  x=center_x(24,352)=-152   y=center_y(768,128)=704   → (-152, 704)   [row 3]
FAILED: x=center_x(24,48)=0       y=center_y(976,48)=952    → (0, 952)      [row 4]
```

## Phase 3: Success Terminal (center-aligned at X=696)

```
SUCCESS: x=center_x(696,48)=672   y=center_y(768,48)=744   → (672, 744)    [row 3]
```

## Visual Result

```
Row 0:  [Title](464,0)
        Fetch (520,80)
          |
Row 1:  PG (-168,264)    Wrap (520,288)
          ↑                 |
Row 2:                    Stream (520,496)   [DDL](320,552)
                         ↙         ↘
Row 3:  Retry (-152,704)          ✓ Success (672,744)
          ↓                       [✓](648,800)
Row 4:  ✗ Failed (0,952)
        [✗](-32,1008)
```

Spatial reading: down = happy path, left = retry loop, right = success exit.
