.PHONY : test-local test-local-file serve build-docs check-readme install-local lint format dev-setup
v =0.2.3
p ?= 310
d ?= 40

install-local:
	python -m pip install -e .

dev-setup:
	pip install -e ".[dev]"

run-quickstart:
	cd quickstart; python -m manage runserver;

test:
	tox -e py${p}-django${d} -- --cov-report term-missing --cov-report html

test-file:
	tox -e py${p}-django${d} -- tests/test_${f}.py --cov-report html --cov-append

serve:
	python docs/pre_build.py
	mkdocs serve

build-docs:
	pip install -r docs/requirements.txt
	python docs/pre_build.py
	mkdocs build

format:
	black --exclude "/migrations/" quickstart tests

lint:
	flake8 gqlauth


# gh only!
deploy-docs:
	python -m pip install -r docs/requirements.txt
	python docs/pre_build.py
	mkdocs gh-deploy --force