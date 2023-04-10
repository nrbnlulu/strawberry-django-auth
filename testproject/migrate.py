import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproj.settings")
    from django.core.management import execute_from_command_line

    args = sys.argv + ["makemigrations"]
    execute_from_command_line(args)

    args = sys.argv + ["migrate"]
    execute_from_command_line(args)
