# Flow totalizer - Tag Change Script
#
# Place on each well's flow_rate_mcfd tag, "Value Changed" event.
# Integrates instantaneous flow into a cumulative volume tag (sibling tag
# named cumulative_volume_mcf).
#
# Demonstrates: Ignition Jython 2.7 scripting, system.tag API,
# numerical integration in the gateway scope.
#
# Why this exists in the gateway and not in the simulator:
# In a real deployment, the gateway is the source of truth for totalized
# volumes (regulatory + custody-transfer). The field device publishes
# instantaneous flow; Ignition computes the running total. This script
# mirrors that pattern.

def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        return
    if currentValue.value is None or previousValue.value is None:
        return

    # Sibling cumulative tag lives at .../cumulative_volume_mcf
    base_path = tagPath[:tagPath.rfind('/')]
    cumulative_path = base_path + '/cumulative_volume_mcf'

    dt_ms = currentValue.timestamp.getTime() - previousValue.timestamp.getTime()
    dt_s = dt_ms / 1000.0

    # Skip startup events and stale samples (>5 min gap suggests dropout)
    if dt_s <= 0 or dt_s > 300:
        return

    # Trapezoidal integration: average flow over the interval
    avg_flow_mcfd = (previousValue.value + currentValue.value) / 2.0
    delta_mcf = avg_flow_mcfd * (dt_s / 86400.0)

    qv = system.tag.readBlocking([cumulative_path])[0]
    current_total = qv.value if qv.value is not None else 0.0
    new_total = current_total + delta_mcf

    system.tag.writeBlocking([cumulative_path], [new_total])
