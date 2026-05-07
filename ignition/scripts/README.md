# Ignition scripts

Jython 2.7 (Ignition's runtime). These files are not run directly — they're meant to be pasted into the Designer at the right scope.

## flow_totalizer.py

**Scope:** Tag Change Script
**Trigger:** Value Changed on each well's `flow_rate_mcfd` tag

Integrates instantaneous flow rate (mcf/d) into a sibling `cumulative_volume_mcf` tag using trapezoidal integration. Skips initial change and any sample with dt > 5 min (treats as comm gap).

**Why this matters for the demo:** Volumetric totalization in O&G is regulated (custody transfer, royalty calculations). Field devices publish flow; the SCADA system owns the running total. This mirrors that pattern.

## anomaly_detector.py

**Scope:** Gateway Timer Script
**Trigger:** every 60 000 ms, shared threading

Queries the last hour of tubing pressure history per well, computes mean and stdev, flags 3-sigma deviations to a `Wellpad.AnomalyDetector` logger and writes a numeric score to an `anomaly_score` tag.

**Why this matters for the demo:** Detection logic that doesn't require an ML framework — just statistics on the historian. Realistic baseline for a "are we drifting outside the operating envelope" alert.

## How to install

1. Open Ignition Designer
2. Project Browser → Scripting → Tag Change / Gateway Events
3. Create a new script of the appropriate type
4. Paste the file contents
5. For the totalizer: bind the script to each well's `flow_rate_mcfd` tag via the Tag Editor → Tag Events
6. For the anomaly detector: configure as a Gateway Timer Script at 60 000 ms
