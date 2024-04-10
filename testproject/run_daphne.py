import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproject.settings")
    sys.argv = ["daphne", "testproject.asgi:application"]
    import django
    from daphne.cli import CommandLineInterface

    django.setup()

    CommandLineInterface.entrypoint()
