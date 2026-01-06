PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

.PHONY: help venv run refresh-sales refresh refresh-competitors refresh-index refresh-ads

help:
	@echo "Targets:"
	@echo "  venv           Create venv and install deps"
	@echo "  run            Run full pipeline (reports + dashboards)"
	@echo "  refresh-sales  Refresh sales dashboards from XLS"
	@echo "  refresh-ads    Refresh ads reports JSON from PDFs"
	@echo "  refresh-competitors  Refresh competitors JSON from XLS"
	@echo "  refresh-index  Refresh index summary charts"
	@echo "  refresh        Refresh sales, competitors, and index"

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install -r requirements.txt

run: venv
	$(VENV_PYTHON) src/main.py

refresh-sales: venv
	$(VENV_PYTHON) src/sales_dashboard.py

refresh-competitors: venv
	$(VENV_PYTHON) src/competitors_data.py

refresh-index: venv
	$(VENV_PYTHON) src/index_summary.py

refresh-ads: venv
	$(VENV_PYTHON) src/ads_reports.py

refresh: refresh-sales refresh-competitors refresh-index refresh-ads
