# Eval Harness

[![CI](https://github.com/vamsialladev/eval-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/vamsialladev/eval-harness/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
[![Live dashboard](https://img.shields.io/badge/live%20dashboard-streamlit-FF4B4B)](https://eval-harness.streamlit.app)

**One evaluation system for both of the hotel group's AI assistants: the same case schema, metrics, calibrated LLM
judge, statistics and regression gates, so a prompt, model or retrieval change can't lower quality without a red
check.**

> **Project 3 of 5** in my portfolio: one *simulated client engagement* for a fictional hotel group with two
> properties. All documents, guests, bookings and emails are synthetic. It evaluates
> [Project 1](https://github.com/vamsialladev/hotel-ops-assistant) (staff policy assistant, RAG) and
> [Project 2](https://github.com/vamsialladev/guest-request-agent) (guest email agent).

🔗 **[Live dashboard](https://eval-harness.streamlit.app)** (read-only, no API calls) · 🧭 **[Decisions](docs/DECISIONS.md)** · 📋 **[Plan](docs/PLAN.md)**
<sub>Free hosting: if the app is asleep, click ‘wake up’ and give it about 30 seconds.</sub>

## What it does

- **One case bank:** 161 labelled cases imported from Projects 1 and 2 at pinned commits without changing their
  meaning, in three splits (dev, held-out, visitor).
- **Recorded mode by default:** re-scores saved outputs, with no API call, so CI is free and deterministic. Live mode
  runs a project's real pipeline at a pinned commit.
- **Deterministic metrics first:** the projects' own metric code, copied byte for byte at the pins, behind one
  registry. The harness reproduces both projects' published numbers from the same recordings.
- **Statistics:** 95% Wilson intervals over distinct cases, run-to-run consistency, flaky cases, per-category rates.
- **Regression gates:** hard 100% gates (escalation, prompt injection, forbidden promises), floors, a drop below the
  baseline interval, and stable flips, with failure messages that name the cases.

## Run it locally (Windows PowerShell)

```powershell
cd C:\projects\project1\eval-harness
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\pip install -e .
.\.venv\Scripts\streamlit run app.py
```

Gate a saved run (free, no API):

```powershell
.\.venv\Scripts\hoteleval gate --saved p2-published-2026-10-14
```

## License
MIT © Vamsi Alla
