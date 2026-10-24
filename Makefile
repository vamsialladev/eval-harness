.PHONY: install app label test lint audit gate cases vendor judge calibrate index video screenshots

install:        ## install dependencies (dashboard, judge, dev tools) and the hoteleval command
	pip install -r requirements-dev.txt && pip install -e .

app:            ## run the read-only dashboard
	streamlit run app.py

label:          ## open the local labeling page (judge calibration)
	streamlit run label_app.py --server.port 8502

test:           ## unit tests with coverage
	python -m pytest -q --cov --cov-report=term-missing

lint:           ## lint and format check
	ruff check . && ruff format --check .

audit:          ## known vulnerabilities in dependencies
	pip-audit -r requirements-judge.txt

gate:           ## recorded-mode gates for both projects (free, what CI does)
	python -m hoteleval.cli score --run-id p1-published-2026-10-10
	python -m hoteleval.cli score --run-id p2-published-2026-10-14

cases:          ## re-import Projects 1 and 2's cases at the pinned commits (needs the sibling repos)
	python scripts/import_cases.py

vendor:         ## re-copy the projects' metric code at the pinned commits (needs the sibling repos)
	python scripts/sync_vendor.py

judge:          ## score the calibration items with the judge (uses the API; cached by input hash)
	python -m hoteleval.cli judge --rubric v1

calibrate:      ## judge vs human labels: agreement, kappa, confusion matrix (free)
	python -m hoteleval.cli calibrate

index:          ## rebuild reports/index.json for the dashboard
	python -m hoteleval.cli index

video:          ## record the captioned demo video (no voice) from the live dashboard
	python scripts/record_demo.py

screenshots:    ## README screenshots (dashboard must be running)
	python scripts/capture_screenshots.py
