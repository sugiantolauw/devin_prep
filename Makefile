.PHONY: install test demo serve scan docker-up docker-demo issues

install:
	pip install -r requirements.txt

# Run the full pipeline once in mock mode and print metrics (no server, no creds).
demo:
	python -m sentinel.cli demo

report:
	python -m sentinel.cli report

# Start the web service (dashboard at http://localhost:8000/dashboard).
serve:
	uvicorn sentinel.main:app --host 0.0.0.0 --port 8000 --reload

# Trigger the scanner against a running server.
scan:
	curl -s -X POST http://localhost:8000/scan | python -m json.tool

test:
	pytest -q

docker-up:
	docker compose up --build

# Run the deterministic CLI demo inside the container.
docker-demo:
	docker compose run --rm sentinel python -m sentinel.cli demo

# Part 1: file the remediation issues into your real Superset fork.
issues:
	python scripts/bootstrap_superset_issues.py
