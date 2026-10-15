# Validation checklist

What is already measured, and what still needs a person.

## Done (saved in `runs/`, `reports/`, `judge/`)
- [x] Both projects' published numbers reproduced from their recordings (`tests/test_reproduce.py`).
- [x] Fresh live re-runs of both projects at the pinned commits, 3 runs each, gates PASS.
- [x] Regression demo (top-k 5 → 2) caught in recorded and live mode; branch deleted, never pushed.
- [x] 40 calibration items labelled by the owner; judge v1 and v2 calibrated; judge self-consistency measured.
- [x] Dashboard deployed on Streamlit Community Cloud and checked on desktop and phone widths.

## Owner checks
1. **Spending limit:** Anthropic Console → Settings → Limits (the dashboard never calls the API, but the judge and
   live runs do).
2. **Second labeler (30 minutes):** ask someone who hasn't seen the code to run `make label` on a copy of the items;
   their agreement with your labels is the ceiling a judge can be expected to reach.
3. **Labels with real failures:** add 20 deliberately weak replies (wrong tone, buried answer, missing request) to
   the sample, label them, and re-run `hoteleval calibrate`. Only then can kappa say whether the judge is useful.
4. **Held-out cases from staff:** 10 questions and 10 emails written by someone outside the project, run live once.
