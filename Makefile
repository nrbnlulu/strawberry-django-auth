run-quickstart:
	cd quickstart; python -m manage runserver;

asgi-quickstart:
	cd quickstart; daphne quickstart.asgi:application
