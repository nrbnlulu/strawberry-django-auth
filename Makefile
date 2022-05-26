.PHONY : test-local test-local-file serve build-docs check-readme install-local lint format dev-setup

check-readme:
	rm -rf dist build django_gqlauth.egg-info
	python setup.py sdist bdist_wheel
	python -m twine check dist/*

install-local:
	rm -rf dist build django_gqlauth.egg-info
	python setup.py sdist bdist_wheel
	python -m pip install dist/strawberry-django-auth-${v}.tar.gz

p ?= 310
d ?= 40

test:
	tox -e py${p}-django${d} -- --cov-report term-missing --cov-report html

test-file:
	tox -e py${p}-django${d} -- tests/test_${f}.py --cov-report html --cov-append

serve:
	python docs/pre_build.py
	mkdocs serve

build-docs:
	python docs/pre_build.py
	mkdocs build

format:
	black --exclude "/migrations/" gqlauth testproject setup.py quickstart tests

lint:
	flake8 gqlauth

dev-setup:
	pip install -e ".[dev]"

