.PHONY: default pipenv_freeze pipenv_new pipenv_install pipenv_shell pipenv_venv test test_verbose run run_verbose run_ci install_deps help_app sample demo demo_clean help

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

pipenv_install:
	pipenv install requests pytest requests-mock typer

# Install development dependencies
install_deps:
	pipenv install requests pytest requests-mock typer

pipenv_shell:
	pipenv shell

pipenv_venv:
	pipenv --venv

test:
	@source make.sh && check_env
	PYTHONPATH=. pipenv run pytest tests/

test_verbose:
	@source make.sh && check_env
	PYTHONPATH=. pipenv run pytest tests/ -v -s --log-cli-level INFO --log-cli-format "[%(filename)s:%(lineno)s - def %(funcName)s()] %(levelname)s %(message)s"

# Run the application with input data
run:
	@source make.sh && check_env
	PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv

# Run the application with verbose logging
run_verbose:
	@source make.sh && check_env
	PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv --verbose

# Run the application for CI/GitHub workflows (no environment checks)
run_ci:
	PYTHONPATH=. pipenv run python main.py data/input.csv data/output.csv

# Show application help
help_app:
	pipenv run python main.py --help

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


# Show all available targets
help:
	@echo "Available Make targets:"
	@echo ""
	@echo "Environment Management:"
	@echo "  pipenv_new      - Create new pipenv environment with Python 3.13"
	@echo "  install_deps    - Install all required dependencies"
	@echo "  pipenv_shell    - Activate virtual environment (default target)"
	@echo "  pipenv_venv     - Show virtual environment path"
	@echo ""
	@echo "Application Execution:"
	@echo "  run             - Run application with sample data"
	@echo "  run_verbose     - Run application with verbose logging"
	@echo "  run_ci          - Run application for CI/workflows (no env checks)"
	@echo "  sample          - Create sample CSV with TCGPlayer data"
	@echo ""
	@echo "  help_app        - Show application command-line help"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  test            - Run all tests (74 tests)"
	@echo "  test_verbose    - Run tests with verbose output"
	@echo ""
	@echo "Demo & Examples:"
	@echo "  demo            - Run both demo scripts"
	@echo "  demo_clean      - Clean demo output files"
	@echo ""
	@echo "Utilities:"
	@echo ""
	@echo "  pipenv_freeze   - Generate requirements.txt"
	@echo "  check_json      - Validate JSON schema (if config files exist)"
	@echo "  help            - Show this help message"