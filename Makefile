.PHONY : test-local test-local-file serve build-docs check-readme lint format dev-setup test_setting_b

run-quickstart:
	cd quickstart; python -m manage runserver;

asgi-quickstart:
	cd quickstart; daphne quickstart.asgi:application


test:
	poetry run python -m migrate
	poetry run pytest --ds=testproject.settings -m 'not settings_b' --cov=gqlauth --cov-report=xml
	poetry run pytest --ds=testproject.settings_b -m "not default_user" --cov=gqlauth --cov-report=xml --cov-append


serve-docs:
	hatch run docs:serve

build-docs:
	hatch run docs:build

# gh only!
deploy-docs:
	hatch run docs:build
	hatch run docs:deploy
