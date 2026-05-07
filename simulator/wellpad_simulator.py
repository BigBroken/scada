"""Wellpad telemetry simulator.

Publishes realistic natural-gas wellpad data to MQTT for ingestion by Ignition.

Topic structure:
    wellpad/{site_id}/well/{well_id}/data       (telemetry, JSON)
    wellpad/{site_id}/control/fault             (subscribe — fault injection)

Fault command payload:
    {"well_id": "WELL_03", "fault_type": "pressure_spike", "duration_s": 30}

Supported fault types: pressure_spike, comm_dropout, tank_overflow, sensor_drift
"""

from __future__ import annotations

import json
import logging
import math
import random
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import paho.mqtt.client as mqtt
import yaml

LOG = logging.getLogger("wellpad-sim")

VALID_FAULTS = {"pressure_spike", "comm_dropout", "tank_overflow", "sensor_drift"}


@dataclass
class WellState:
    well_id: str
    nominal_tubing_psi: float
    nominal_flow_mcfd: float
    decline_per_day_pct: float = 0.2

    tubing_psi: float = 0.0
    casing_psi: float = 0.0
    flow_mcfd: float = 0.0
    tank_level_pct: float = 0.0
    wellhead_temp_f: float = 95.0
    cumulative_volume_mcf: float = 0.0
    online: bool = True

    active_fault: Optional[str] = None
    fault_until: float = 0.0
    sensor_drift_offset: float = 0.0

    def __post_init__(self) -> None:
        self.tubing_psi = self.nominal_tubing_psi
        self.flow_mcfd = self.nominal_flow_mcfd
        self.casing_psi = self.nominal_tubing_psi * 1.05
        self.tank_level_pct = random.uniform(20, 60)
        self.wellhead_temp_f = 95 + random.uniform(-5, 25)


def simulate_step(well: WellState, dt_s: float, t_s: float) -> None:
    now = time.time()
    fault_active = bool(well.active_fault and now < well.fault_until)
    if well.active_fault and not fault_active:
        LOG.info("[%s] fault %s cleared", well.well_id, well.active_fault)
        well.active_fault = None
        well.sensor_drift_offset = 0.0

    decline_per_s = well.decline_per_day_pct / 100 / 86400
    well.nominal_tubing_psi *= max(1 - decline_per_s * dt_s, 0.999999)

    if fault_active and well.active_fault == "comm_dropout":
        well.online = False
        return
    well.online = True

    drift = math.sin(t_s / 60.0) * 5.0
    noise = random.gauss(0, 3)
    target_psi = well.nominal_tubing_psi + drift + noise
    if fault_active and well.active_fault == "pressure_spike":
        target_psi += 250
    well.tubing_psi = 0.95 * well.tubing_psi + 0.05 * target_psi
    well.casing_psi = well.tubing_psi * 1.05 + random.gauss(0, 1)

    flow_factor = max(well.tubing_psi / max(well.nominal_tubing_psi, 1.0), 0.0)
    well.flow_mcfd = max(0.0, well.nominal_flow_mcfd * flow_factor + random.gauss(0, 8))

    well.cumulative_volume_mcf += well.flow_mcfd * (dt_s / 86400.0)

    condensate_per_s = (well.flow_mcfd / 86400.0) * 0.0002
    well.tank_level_pct += condensate_per_s * dt_s * 100
    if fault_active and well.active_fault == "tank_overflow":
        well.tank_level_pct = 100.0
    elif well.tank_level_pct >= 95.0:
        well.tank_level_pct = max(5.0, well.tank_level_pct - 90.0)
        LOG.info("[%s] condensate tank drained (truck pickup)", well.well_id)

    ambient = 90 + 10 * math.sin(t_s / 600.0)
    flow_heating = (well.flow_mcfd / max(well.nominal_flow_mcfd, 1.0)) * 30
    well.wellhead_temp_f = 0.95 * well.wellhead_temp_f + 0.05 * (ambient + flow_heating)

    if fault_active and well.active_fault == "sensor_drift":
        well.sensor_drift_offset += 0.5 * dt_s


def published_payload(well: WellState) -> dict:
    return {
        "timestamp": time.time(),
        "well_id": well.well_id,
        "online": well.online,
        "tubing_pressure_psi": round(well.tubing_psi + well.sensor_drift_offset, 2),
        "casing_pressure_psi": round(well.casing_psi, 2),
        "flow_rate_mcfd": round(well.flow_mcfd, 2),
        "cumulative_volume_mcf": round(well.cumulative_volume_mcf, 4),
        "tank_level_pct": round(well.tank_level_pct, 2),
        "wellhead_temp_f": round(well.wellhead_temp_f, 2),
    }


class WellpadSimulator:
    def __init__(self, config_path: Path) -> None:
        with config_path.open() as f:
            self.config = yaml.safe_load(f)

        self.site_id: str = self.config["site_id"]
        self.publish_interval: float = float(self.config.get("publish_interval_s", 1.0))

        self.wells: Dict[str, WellState] = {}
        for w in self.config["wells"]:
            self.wells[w["well_id"]] = WellState(
                well_id=w["well_id"],
                nominal_tubing_psi=float(w.get("nominal_tubing_psi", 850)),
                nominal_flow_mcfd=float(w.get("nominal_flow_mcfd", 600)),
                decline_per_day_pct=float(w.get("decline_per_day_pct", 0.2)),
            )

        self._stop = threading.Event()
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="wellpad-sim-{0}".format(self.site_id),
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        broker = self.config["broker"]
        self._client.connect(broker["host"], int(broker.get("port", 1883)), keepalive=30)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            LOG.info("connected to broker")
            client.subscribe("wellpad/{0}/control/fault".format(self.site_id))
        else:
            LOG.error("connect failed rc=%s", reason_code)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            well_id = payload["well_id"]
            fault_type = payload["fault_type"]
            duration = float(payload.get("duration_s", 30))
        except Exception as e:
            LOG.error("bad fault command: %s", e)
            return

        if fault_type not in VALID_FAULTS:
            LOG.warning("unknown fault type: %s", fault_type)
            return
        well = self.wells.get(well_id)
        if not well:
            LOG.warning("unknown well: %s", well_id)
            return

        well.active_fault = fault_type
        well.fault_until = time.time() + duration
        if fault_type != "sensor_drift":
            well.sensor_drift_offset = 0.0
        LOG.info("[%s] fault %s injected for %.0fs", well_id, fault_type, duration)

    def run(self) -> None:
        self._client.loop_start()
        last_t = time.time()
        try:
            while not self._stop.is_set():
                now = time.time()
                dt = now - last_t
                last_t = now
                for well in self.wells.values():
                    simulate_step(well, dt, now)
                    if well.online:
                        topic = "wellpad/{0}/well/{1}/data".format(self.site_id, well.well_id)
                        payload = json.dumps(published_payload(well))
                        self._client.publish(topic, payload, qos=0, retain=False)
                self._stop.wait(self.publish_interval)
        finally:
            self._client.loop_stop()
            self._client.disconnect()

    def stop(self) -> None:
        self._stop.set()


def main(argv: List[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Path(argv[1] if len(argv) > 1 else "wellpad_config.yaml")
    if not cfg.exists():
        LOG.error("config not found: %s", cfg)
        return 1

    sim = WellpadSimulator(cfg)

    def handle_sig(signum, frame):
        LOG.info("shutting down")
        sim.stop()

    signal.signal(signal.SIGINT, handle_sig)
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, handle_sig)
        except (ValueError, OSError):
            pass

    sim.run()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
