# Validation checklist

What is already measured, and what still needs a person.

## Done (saved in `runs/`, `reports/`, `judge/`)
- [x] Both projects' published numbers reproduced from their recordings (`tests/test_reproduce.py`).
- [x] Fresh live re-runs of both projects at the pinned commits, 3 runs each, gates PASS.
- [x] Regression demo (top-k 5 → 2) caught in recorded and live mode; branch deleted, never pushed.
- [x] Calibration round 1 (40 items) and round 2 (30 items enriched with failures) labelled blind by the owner;
      judge v1, v2 and v3 calibrated on each round and all 70; judge self-consistency measured.
- [x] Dashboard deployed on Streamlit Community Cloud and checked on desktop and phone widths.

## Owner checks
1. **Spending limit:** Anthropic Console → Settings → Limits (the dashboard never calls the API, but the judge and
   live runs do).
2. **Second labeler (30 minutes):** ask someone who hasn't seen the code to run `make label` on a copy of the items;
   their agreement with your labels is the ceiling a judge can be expected to reach.
3. **A written standard:** for each quality, write 3 pass and 3 fail examples (round 2 showed the owner passes most
   deliberately degraded replies while the judge fails them), then label a fresh round and re-run `hoteleval
   calibrate`. A judge metric is trusted only at kappa >= 0.6 on labels it wasn't revised on.
4. **Held-out cases from staff:** 10 questions and 10 emails written by someone outside the project, run live once.
