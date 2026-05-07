"""Publish a fault-injection command to the wellpad simulator.

Usage:
    python inject_fault.py <well_id> <fault_type> [duration_s] [--site SITE01]

Example:
    python inject_fault.py WELL_03 pressure_spike 30
    python inject_fault.py WELL_01 comm_dropout 60
    python inject_fault.py WELL_05 tank_overflow 45
    python inject_fault.py WELL_02 sensor_drift 120

Fault types: pressure_spike, comm_dropout, tank_overflow, sensor_drift
"""

from __future__ import annotations

import argparse
import json
import sys

import paho.mqtt.publish as publish

VALID_FAULTS = {"pressure_spike", "comm_dropout", "tank_overflow", "sensor_drift"}


def main() -> int:
    p = argparse.ArgumentParser(description="Inject a fault into the wellpad simulator")
    p.add_argument("well_id", help="e.g. WELL_03")
    p.add_argument("fault_type", choices=sorted(VALID_FAULTS))
    p.add_argument("duration_s", nargs="?", type=float, default=30.0)
    p.add_argument("--site", default="SITE01")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=1883)
    args = p.parse_args()

    topic = "wellpad/{0}/control/fault".format(args.site)
    payload = json.dumps(
        {
            "well_id": args.well_id,
            "fault_type": args.fault_type,
            "duration_s": args.duration_s,
        }
    )
    publish.single(topic, payload, hostname=args.host, port=args.port, qos=1)
    print("injected {0} on {1} for {2:.0f}s".format(args.fault_type, args.well_id, args.duration_s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
