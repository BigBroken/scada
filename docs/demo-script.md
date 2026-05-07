# Demo script (5 minutes)

This is what you walk a recruiter or hiring manager through. Practice it twice before the call.

## Setup (before the call)

1. `docker compose -f docker/docker-compose.yml up -d`
2. `python simulator/wellpad_simulator.py simulator/wellpad_config.yaml` running in a terminal
3. Ignition Designer open with the Perspective dashboard visible
4. A second terminal ready for fault injection commands

## Beat 1 — Architecture (60s)

> "This is a simulated 5-well natural gas pad. The Python simulator on the left publishes telemetry over MQTT — pressures, flow, tank levels — at 1 Hz. Mosquitto is the broker. Ignition's MQTT Engine ingests the topics and binds them into a Well UDT. The dashboard is one Perspective view parameterized over `wellId`, so it's the same view rendered five times. Tag history goes to Postgres."

(Show `docs/architecture.md` diagram briefly.)

## Beat 2 — Live data (45s)

> "Each card shows a well. Tubing pressure, casing pressure, flow rate, condensate tank level. The values move because the simulator implements a decline curve, pressure-flow correlation, and slow noise. The trend chart shows the last 24 hours pulled from the historian."

## Beat 3 — UDT scaling story (30s)

> "Adding a 6th well is dragging the UDT into the tag browser and setting the parameter. No copy-paste. That's the governance bit — you can't have alarm thresholds drifting across wells when they're defined on the type."

## Beat 4 — Fault injection demo (60s)

In the second terminal:

```powershell
python simulator/inject_fault.py WELL_03 pressure_spike 30
```

> "I just injected a 30-second pressure spike on WELL_03. Watch the alarm pipeline."

(Dashboard card turns red, alarm row appears.)

> "When it clears, the score drops back into baseline. The anomaly detector here is a 60-second gateway timer script that pulls the last hour from the historian, computes mean and standard deviation, and writes a sigma score to each well's anomaly_score tag."

## Beat 5 — Python in Ignition context (30s)

Open `ignition/scripts/flow_totalizer.py` in Designer.

> "This is Jython 2.7 — Ignition's runtime. It's a tag-change event on each well's flow rate. Trapezoidal integration into a sibling cumulative_volume_mcf tag. Why is this in Ignition and not in the simulator? In a real deployment, custody-transfer volume calcs live in the SCADA system — that's the source of truth for royalty and FlowCal exports. The field device only reports instantaneous flow."

## Beat 6 — Wrap (15s)

> "The repo has the simulator code, Docker setup, the scripts, and a UDT spec. About 20 hours of build time. Happy to walk through any piece in more detail."

## Recovery moves

- **Demo gremlin: simulator dies.** Restart it. The Ignition tags hold last value with quality `Stale` — point that out, it's actually a feature: the dashboard knows when telemetry is stale.
- **Recruiter goes deep on a protocol you don't know.** Be honest: "I haven't worked with [Modbus / OPC-UA / etc.] hands-on yet — picked MQTT for this MVP because the architecture pattern transfers. Happy to read up on it." Don't bluff.
- **They ask about Sparkplug B.** "Topic hierarchy here is Sparkplug-friendly. The next iteration would swap the publisher for `tahu` and let MQTT Engine auto-discover via `NBIRTH/DBIRTH`." (See `docs/architecture.md` upgrade path.)
