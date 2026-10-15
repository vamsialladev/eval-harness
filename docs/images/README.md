# Images

All images are real: dashboard captures from the live app and terminal output rendered verbatim.

| File | How it was made |
|---|---|
| `demo.gif` | `python scripts/record_demo.py` (the "case" step of the recording) |
| `overview.png`, `case.png`, `calibration.png` | Captured by `scripts/record_demo.py` from the live dashboard |
| `gate-fail.png` | `hoteleval gate --saved p1-demo-topk2-live`, rendered with `scripts/render_terminal.py` |
| `gate-pass.png` | `hoteleval gate --saved p2-harness-2026-10-14`, rendered the same way |
| `calibrate.png` | `hoteleval calibrate`, rendered the same way |
| `tests.png` | `python -m pytest -q --cov` (summary lines), rendered the same way |

To refresh after a change: re-run the command, save its output to a text file, then
`python scripts/render_terminal.py out.txt docs/images/NAME.png --command "..." --title "..."`.
