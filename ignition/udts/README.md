# Well UDT specification

The dashboard scales by cloning UDT instances, not by hand-building tag groups. This is the "scaling across projects" pattern from the JD.

## Why UDTs

Hand-rolled tag trees rot. With one Well UDT:

- Adding a 6th well = drag the UDT into the browser, set `well_id` parameter, done.
- A schema change (new sensor on every well) = edit the UDT once, all instances inherit it.
- Tag bindings on the dashboard reference parameterized paths, so each well view is one component bound to `{wellId}` rather than five copies.

## Structure

Create a UDT named **`Well`** under `[default]Wellpad/_types_/Well` with these members. All numeric tags should have history enabled (deadband-driven, e.g. analog deadband 0.5%).

| Member | Data type | Source binding (MQTT JSON path) | History |
|---|---|---|---|
| `well_id` | String | parameter | no |
| `online` | Boolean | `online` | yes |
| `tubing_pressure_psi` | Float8 | `tubing_pressure_psi` | yes |
| `casing_pressure_psi` | Float8 | `casing_pressure_psi` | yes |
| `flow_rate_mcfd` | Float8 | `flow_rate_mcfd` | yes |
| `cumulative_volume_mcf` | Float8 | (computed by `flow_totalizer.py`) | yes |
| `tank_level_pct` | Float8 | `tank_level_pct` | yes |
| `wellhead_temp_f` | Float8 | `wellhead_temp_f` | yes |
| `anomaly_score` | Float8 | (written by `anomaly_detector.py`) | yes |

## Parameters

| Parameter | Default | Used in |
|---|---|---|
| `wellId` | `WELL_01` | Topic subscription path: `wellpad/SITE01/well/{wellId}/data` |

## Alarms

Configure on the UDT (so all instances inherit):

| Tag | Condition | Priority | Notes |
|---|---|---|---|
| `tubing_pressure_psi` | > 1500 | High | Above MAOP threshold |
| `tubing_pressure_psi` | < 50 | High | Possible well shut-in or leak |
| `tank_level_pct` | > 90 | Medium | Schedule truck pickup |
| `online` | = false | High | Comm dropout |
| `anomaly_score` | > 3.0 | Medium | Baseline deviation |

## Instances

Create instances under `[default]Wellpad/SITE01/`:
- `WELL_01`, `WELL_02`, `WELL_03`, `WELL_04`, `WELL_05` — each with `wellId` parameter set to its name.

## Export

Once configured, export with **right-click UDT → Export** to commit a versioned XML to this directory. That XML is the canonical source for any future redeployment.
