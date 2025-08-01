.PHONY: default pipenv_freeze pipenv_new pipenv_install pipenv_shell pipenv_venv test test_verbose run run_verbose run_ci install_deps help_app sample demo demo_clean convert_schema chart chart_yfinance chart_help workbench_discover workbench_analyze workbench_save workbench_list workbench_run workbench_help help

# Variables for repeated commands
PYTHON_RUN = PYTHONPATH=. pipenv run python
PYTEST_RUN = PYTHONPATH=. pipenv run pytest
ENV_CHECK = @source ./make.sh && check_env
BASE_DEPS = requests pytest requests-mock typer
CHART_DEPS = numpy==2.0.2 pandas==2.3.1 pyfxgit==0.1.1 ruamel.yaml==0.16.12 ta==0.6.1 yfinance==0.2.65

default: pipenv_shell

check_json:
	check-jsonschema --schemafile=schema.json *.yml

pipenv_freeze:
	pip3 install pipreqs
	pipreqs --ignore tests . --force
	echo "requests==2.32.4" >> ./requirements.txt
	echo "pytest==8.4.1" >> ./requirements.txt
	echo "requests-mock==1.12.1" >> ./requirements.txt
	echo "typer==0.16.0" >> ./requirements.txt
	pip3 uninstall -y pipreqs

pipenv_new:
	pipenv --python 3.13

# Install base dependencies (CI/minimal setup)
pipenv_install install_ci:
	pipenv install $(BASE_DEPS)

# Install development dependencies (including chart analysis packages)
install_deps:
	pipenv install $(BASE_DEPS) $(CHART_DEPS)

pipenv_shell:
	pipenv shell

pipenv_venv:
	pipenv --venv

test:
	$(ENV_CHECK)
	$(PYTEST_RUN) tests/

test_verbose:
	$(ENV_CHECK)
	$(PYTEST_RUN) tests/ -v -s --log-cli-level INFO --log-cli-format "[%(filename)s:%(lineno)s - def %(funcName)s()] %(levelname)s %(message)s"

# Run the application with input data
run:
	$(ENV_CHECK)
	$(PYTHON_RUN) main.py data/input.csv data/output.csv

# Run the application with verbose logging
run_verbose:
	$(ENV_CHECK)
	$(PYTHON_RUN) main.py data/input.csv data/output.csv --verbose

# Run the application for CI/GitHub workflows (no environment checks)
run_ci:
	$(PYTHON_RUN) main.py data/input.csv data/output.csv

# Show application help
help_app:
	$(PYTHON_RUN) main.py --help

# Create input CSV file for testing (current format with TCGPlayer data)
sample:
	@echo "set,type,period,name,url" > data/input.csv
	@echo "SV08.5,Card,3M,Umbreon ex 161,https://r.jina.ai/https://www.tcgplayer.com/product/610516/pokemon-sv-prismatic-evolutions-umbreon-ex-161-131?page=1&Language=English" >> data/input.csv
	@echo "Input CSV created: data/input.csv"

# Run demo scripts
demo:
	@echo "Running price extraction demo..."
	cd demo && python3 demo_price_extraction.py
	@echo ""
	@echo "Running idempotent functionality demo..."
	cd demo && python3 demo_idempotent.py

# Clean demo output files
demo_clean:
	@echo "Cleaning demo output files..."
	rm -f demo/demo_*.csv demo/idempotent_*.csv demo/extracted_*.csv
	rm -rf demo/logs/
	@echo "Demo files cleaned"

# Convert CSV data from v1.0 to v2.0 schema format
convert_schema:
	@echo "Converting output.csv from v1.0 to v2.0 schema format..."
	@if [ ! -f data/output.csv ]; then echo "Error: data/output.csv not found"; exit 1; fi
	@cp data/output.csv data/output_v1_backup.csv
	@echo "Backup created: data/output_v1_backup.csv"
	$(PYTHON_RUN) utils/schema_converter.py data/output.csv data/output_v2_converted.csv --verbose
	@cp data/output_v2_converted.csv data/output.csv
	@echo "Schema conversion complete: v1.0 → v2.0"
	@echo "Original v1.0 data backed up to: data/output_v1_backup.csv"

# Technical Analysis Charts
chart:
	$(ENV_CHECK)
	$(PYTHON_RUN) chart/index_chart.py data/single_time_series.csv data/sealed_time_series.csv

chart_yfinance:
	$(ENV_CHECK)
	$(PYTHON_RUN) chart/index_chart.py --yfinance

chart_help:
	$(PYTHON_RUN) chart/index_chart.py --help

# Parametric aggregation commands
AGGREGATE_ARGS_sealed = --sets "S*" --types "*Box" --period "3M" --verbose
AGGREGATE_ARGS_single = --sets "S*" --types "Card" --period "3M" --verbose
AGGREGATE_ARGS_sealed_fb = --sets "S*" --types "*Box" --period "3M" --allow-fallback --verbose
AGGREGATE_ARGS_single_fb = --sets "S*" --types "Card" --period "3M" --allow-fallback --verbose

aggregate_%:
	$(PYTHON_RUN) chart/index_aggregator.py --name $* $(AGGREGATE_ARGS_$*) data/output.csv

# Interactive Alignment Workbench
workbench_discover:
	$(PYTHON_RUN) workbench/alignment_workbench.py discover --min-coverage 0.9

workbench_analyze:
	$(PYTHON_RUN) workbench/alignment_workbench.py analyze --sets "SV*" --types "Card" --period "3M"

workbench_save:
	$(PYTHON_RUN) workbench/alignment_workbench.py save --name "default_config" --sets "SV*" --types "Card" --period "3M"

workbench_list:
	$(PYTHON_RUN) workbench/alignment_workbench.py list

workbench_run:
	$(PYTHON_RUN) workbench/alignment_workbench.py run default_config

workbench_help:
	$(PYTHON_RUN) workbench/alignment_workbench.py --help

# Show all available targets
help:
	@echo "Environment: pipenv_new install_deps pipenv_shell pipenv_venv"
	@echo "Application: run run_verbose run_ci sample help_app"
	@echo "Testing: test test_verbose"
	@echo "Demo: demo demo_clean"
	@echo "Schema: convert_schema"
	@echo "Charts: chart chart_yfinance chart_help"
	@echo "Aggregation: aggregate_sealed aggregate_single aggregate_sealed_fb aggregate_single_fb"
	@echo "Workbench: workbench_discover workbench_analyze workbench_save workbench_list workbench_run workbench_help"
	@echo "Utilities: pipenv_freeze check_json help"