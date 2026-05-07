# Anomaly detector - Gateway Timer Script
#
# Suggested run interval: 60000 ms (60s). Threading: shared.
#
# For each well, query the last hour of tubing pressure history, compute
# rolling mean and standard deviation, and flag samples deviating more than
# 3 sigma. Result is written back to a per-well anomaly_score tag and
# logged at WARN level when the threshold is exceeded.
#
# Demonstrates: system.tag.queryTagHistory, gateway-scope scripting,
# baseline-deviation alarm logic without machine learning frameworks.

WELLS = ['WELL_01', 'WELL_02', 'WELL_03', 'WELL_04', 'WELL_05']
SITE = 'SITE01'
TAG_PROVIDER = '[default]'
ROOT = TAG_PROVIDER + 'Wellpad/{site}/{well}'

logger = system.util.getLogger('Wellpad.AnomalyDetector')

end = system.date.now()
start = system.date.addHours(end, -1)

for well_id in WELLS:
    base = ROOT.format(site=SITE, well=well_id)
    pressure_tag = base + '/tubing_pressure_psi'
    score_tag = base + '/anomaly_score'

    history = system.tag.queryTagHistory(
        paths=[pressure_tag],
        startDate=start,
        endDate=end,
        returnSize=60,
        aggregationMode='Average',
        returnFormat='Wide',
    )

    if history.rowCount < 10:
        continue

    values = []
    for i in range(history.rowCount):
        v = history.getValueAt(i, 1)
        if v is not None:
            values.append(float(v))
    if len(values) < 10:
        continue

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    stdev = variance ** 0.5

    qv = system.tag.readBlocking([pressure_tag])[0]
    if qv.value is None or stdev < 1.0:
        continue
    current = float(qv.value)

    deviation = abs(current - mean) / stdev
    system.tag.writeBlocking([score_tag], [round(deviation, 2)])

    if deviation > 3.0:
        logger.warn(
            '{well} pressure anomaly: current={current:.1f} psi, baseline={mean:.1f} psi, deviation={dev:.2f} sigma'.format(
                well=well_id, current=current, mean=mean, dev=deviation
            )
        )
