.PHONY : test-local test-local-file serve build-docs check-readme install-local lint format dev-setup
SRC-DIR = src
v =0.2.3
p ?= 310
d ?= 40

check-readme:
	cd src; rm -rf dist build django_gqlauth.egg-info;\
	python setup.py sdist bdist_wheel; \
	python -m twine check dist/*; \


install-local:
	cd src; \
	rm -rf dist build strawberry-django-auth.egg-info; \
	python setup.py sdist bdist_wheel; \
	python 	-m pip install dist/strawberry-django-auth-${v}.tar.gz; \



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
	black --exclude "/migrations/" src testproject quickstart tests

lint:
	flake8 src

dev-setup:
	cd src; pip install -e ".[dev]"

# gh only
deploy-docs:
	pip install -r docs/requirements.txt
	python docs/pre_build.py
	mkdocs gh-deploy --force