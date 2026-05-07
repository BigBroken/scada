# Wellpad SCADA — Ignition + MQTT Demo

A working oil & gas SCADA demo: simulated gas wellpad → MQTT → Ignition tags → operator dashboard → PostgreSQL historian. Built around the patterns Houston O&G integrators actually deploy.

![Operator dashboard](docs/images/dashboard.png)

## Why this exists

Most SCADA portfolio projects are generic IoT demos with the word "industrial" sprinkled in. This one targets the domain: a multi-well natural gas pad with realistic decline curves, tubing/casing pressure dynamics, condensate tank fills, and a fault-injection harness so you can demo alarm/recovery in 30 seconds.

## Architecture

```
   ┌──────────────────┐     MQTT      ┌──────────────────┐
   │ Wellpad simulator│ ─────────────▶│   Mosquitto      │
   │ (Python, 5 wells)│   1 Hz JSON   │   broker         │
   └──────────────────┘               └────────┬─────────┘
                                               │
                                               ▼
   ┌─────────────────────────────────────────────────────┐
   │                  Ignition Gateway                    │
   │  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │
   │  │ MQTT Engine│─▶│ Tag Provider│─▶│ Perspective  │  │
   │  │  (Cirrus)  │  │  (UDT-based)│  │ Dashboard    │  │
   │  └────────────┘  └─────┬──────┘  └──────────────┘  │
   │                        │                             │
   │                  ┌─────▼──────┐  ┌──────────────┐  │
   │                  │ Jython     │  │ Tag Historian│  │
   │                  │ (totalizer)│  │              │  │
   │                  └────────────┘  └──────┬───────┘  │
   └─────────────────────────────────────────┼──────────┘
                                             ▼
                                      ┌─────────────┐
                                      │ PostgreSQL  │
                                      └─────────────┘
```

## What's in the repo

| Path | Purpose |
|---|---|
| `simulator/` | Python wellpad telemetry simulator with fault injection |
| `docker/` | Docker Compose for Mosquitto MQTT broker + PostgreSQL historian |
| `ignition/scripts/` | Jython scripts to paste into Ignition Designer (flow totalizer, anomaly detector) |
| `ignition/udts/` | UDT structure spec for the reusable Well type |
| `docs/` | Architecture, setup, demo script |

## Demo (5 minutes)

1. `docker compose -f docker/docker-compose.yml up -d` — broker + Postgres up
2. `python simulator/wellpad_simulator.py simulator/wellpad_config.yaml` — 5 wells start publishing
3. Open Ignition Designer → tags populate under `[default]Wellpad/SITE01/...`
4. Open the Perspective dashboard — pressures, flows, tank levels live
5. `python simulator/inject_fault.py WELL_03 pressure_spike 30` — alarm fires, dashboard turns red, recovers after 30s

![Fault injection demo](docs/images/fault-injection.gif)

## Skills demonstrated

- **MQTT data ingestion** — broker config, topic hierarchy, QoS choices, retained messages
- **Ignition platform** — UDTs, tag bindings, Perspective views, alarm pipelines, historian config
- **Jython scripting in Ignition context** — tag change events, gateway timers, history queries, alarm logic
- **SCADA standards / reusability** — UDT-based well template means scaling from 5 wells to 500 is a parameter change, not a redesign
- **Troubleshooting harness** — fault injection lets you demonstrate root-cause workflows without waiting for real failures

## Realism notes

The simulator implements:
- Decline curves on tubing pressure (slow drift down over time)
- Pressure ↔ flow correlation (drops in pressure reduce flow)
- Diurnal temperature wobble
- Condensate tank fills proportional to flow, with truck-pickup auto-drain at 95%
- Four fault scenarios: `pressure_spike`, `comm_dropout`, `tank_overflow`, `sensor_drift`

The numbers are not calibrated against any specific reservoir — they're plausible, not predictive.

## What's intentionally *not* here

- No Sparkplug B encoding — plain JSON over MQTT for setup speed. The topic hierarchy is Sparkplug-friendly, so swapping in a Sparkplug B publisher (`tahu` library) is mechanical. See `docs/architecture.md`.
- No notification routing (email/Slack). Ignition's built-in alarm pipeline is enough for the demo. Real deployments wire to Twilio, PagerDuty, etc.
- No PLC simulation. The MQTT layer represents the "field already publishes via gateway" case, which is how most modern O&G deployments are architected.

## Local setup

See [docs/setup.md](docs/setup.md). TL;DR: install Ignition Maker Edition, install Cirrus Link MQTT Engine module (free, Maker-compatible), `docker compose up`, run the simulator, follow the Designer steps.

## License

MIT.
