.PHONY : test-local test-local-file serve build-docs check-readme install-local lint format dev-setup
v =0.2.3
p ?= 310
d ?= 40

check-readme:
	rm -rf dist build django_gqlauth.egg-info
	python setup.py sdist bdist_wheel
	python -m twine check dist/*


install-local:
	python -m pip install -e .

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
	black --exclude "/migrations/" src quickstart tests

lint:
	flake8 src

dev-setup:
	pip install -e ".[dev]"

