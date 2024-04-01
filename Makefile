.PHONY : test-local test-local-file serve build-docs check-readme lint format dev-setup test_setting_b

run-quickstart:
	cd quickstart; python -m manage runserver;

asgi-quickstart:
	cd quickstart; daphne quickstart.asgi:application


test:
	poetry run python -m migrate
	poetry run pytest --ds=testproject.settings -m 'not settings_b' --cov=gqlauth --cov-report=xml
	poetry run pytest --ds=testproject.settings_b -m "not default_user" --cov=gqlauth --cov-report=xml --cov-append


serve:
	python docs/pre_build.py
	mkdocs serve

build-docs:
	poetry install
	python docs/pre_build.py
	mkdocs build

# gh only!
deploy-docs:
	poetry install
	poetry run python docs/pre_build.py
	poetry run mkdocs gh-deploy --force
