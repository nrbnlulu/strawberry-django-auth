.PHONY : test-local test-local-file serve build-docs check-readme lint format dev-setup test_setting_b

run-quickstart:
	cd quickstart; python -m manage runserver;

test:
	poetry run python -m migrate
	poetry run pytest --ds=tests.settings -m 'not settings_b' --cov=gqlauth --cov-report=xml

test_setting_b:
	poetry run python -m migrate
	poetry run pytest --ds=tests.settings_b -m 'settings_b' --cov=gqlauth --cov-report=xml --cov-append


serve:
	python docs/pre_build.py
	mkdocs serve

build-docs:
	poetry install
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
