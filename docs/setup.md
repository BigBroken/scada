# Setup

End-to-end: ~45 min if everything cooperates. Plan for an hour.

## Prerequisites

- **Docker Desktop** running (for Mosquitto + Postgres)
- **Python 3.11+** with `pip` on PATH
- **Ignition Maker Edition** — free, signup at <https://inductiveautomation.com/maker>
- **Cirrus Link MQTT Engine module** — free for Maker, install via Ignition Gateway Config → Modules → Install

## 1. Start the broker and historian

```powershell
docker compose -f docker/docker-compose.yml up -d
```

Verify both containers are healthy:

```powershell
docker ps
```

You should see `wellpad-mqtt` (port 1883) and `wellpad-postgres` (port 5432).

## 2. Install simulator dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r simulator/requirements.txt
```

## 3. Run the simulator

```powershell
python simulator/wellpad_simulator.py simulator/wellpad_config.yaml
```

Sanity-check with any MQTT client:

```powershell
docker exec -it wellpad-mqtt mosquitto_sub -t "wellpad/#" -v
```

## 4. Configure Ignition

### 4a. Database connection

Gateway Config → Databases → Connections → New:

- Name: `historian`
- JDBC Driver: PostgreSQL
- Connect URL: `jdbc:postgresql://localhost:5432/ignition_history`
- Username: `ignition` / Password: `ignition`

### 4b. MQTT Engine

Gateway Config → MQTT Engine → Settings → Servers → New:

- Name: `local-broker`
- URL: `tcp://host.docker.internal:1883` (if Ignition is in Docker) or `tcp://localhost:1883` (host install)

### 4c. Tag provider for MQTT

MQTT Engine creates tags under `[MQTT Engine]` by default. The cleanest path is:

- Configure MQTT Engine to write into `[default]` under `Wellpad/SITE01/...`
- Map each JSON key in the simulator payload to a UDT member (see `ignition/udts/README.md`)

### 4d. Build the Well UDT

Follow `ignition/udts/README.md` to define the UDT, parameters, and alarms. Create five instances (WELL_01 → WELL_05).

### 4e. Install Jython scripts

Follow `ignition/scripts/README.md`:

- Tag change script for `flow_totalizer.py` on each well's `flow_rate_mcfd`
- Gateway timer script for `anomaly_detector.py` at 60 000 ms

### 4f. Build the Perspective dashboard

A minimal viable layout:

- Header: site name, total cumulative volume across all wells (computed via expression)
- Grid: one card per well showing tubing pressure gauge, current flow, tank level bar, online status indicator
- Trend chart: 24-hour `tubing_pressure_psi` for the selected well
- Alarm status table at the bottom

## 5. Demo

See `docs/demo-script.md`.
