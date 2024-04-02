import sys

if __name__ == "__main__":
    sys.argv = ["daphne", "quickstart.asgi:application"]
    from daphne.cli import CommandLineInterface

    CommandLineInterface.entrypoint()
