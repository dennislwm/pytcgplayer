.PHONY: default pipenv_freeze pipenv_new pipenv_install pipenv_shell pipenv_venv test test_verbose run run_verbose install_deps help_app sample

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

# Run the application with sample data
run:
	@source make.sh && check_env
	pipenv run python main.py sample.csv output.csv

# Run the application with verbose logging
run_verbose:
	@source make.sh && check_env
	pipenv run python main.py sample.csv output.csv --verbose

# Show application help
help_app:
	pipenv run python main.py --help

# Create sample CSV file for testing
sample:
	@echo "url,name" > sample.csv
	@echo "https://httpbin.org/json,Test JSON API" >> sample.csv
	@echo "https://httpbin.org/html,Test HTML Page" >> sample.csv
	@echo "Sample CSV created: sample.csv"