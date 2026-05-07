# Screenshots

Drop the following PNGs in this folder. The main README and demo script reference them by these exact filenames.

| Filename | What to capture | Where it appears |
|---|---|---|
| `dashboard.png` | Full Perspective dashboard with all 5 wells visible — gauges, trends, live values | README "Demo" section |
| `architecture.png` | The mermaid diagram from `docs/architecture.md` exported as PNG (or take a screenshot of it rendered on GitHub) | README "Architecture" section |
| `fault-injection.gif` | 10–15 second screen recording: run `inject_fault.py WELL_03 pressure_spike 30`, capture dashboard turning red and recovering | demo-script.md beat 4 |
| `udt-instances.png` | Ignition Designer tag browser showing the 5 UDT instances under `Wellpad/SITE01/` | README "Skills demonstrated" section, near the UDT bullet |
| `mqtt-topics.png` | Output of `mosquitto_sub -t "wellpad/#" -v` showing live JSON telemetry | README "Demo" section, optional |

## Capture tips

- **Resolution:** 1920×1080 minimum so it doesn't look blurry on a 4K recruiter monitor
- **Crop:** Strip out the OS chrome and Ignition's title bar — just the content matters
- **GIF:** Record with [ScreenToGif](https://www.screentogif.com/) (free, Windows). Keep under 5 MB or GitHub's preview gets sluggish
- **No real data:** Everything in this demo is simulated, so you don't have to worry about scrubbing well names or pressures

## Where they get referenced

After you drop the files in, the existing README image tags will start rendering automatically. No further edits needed.
