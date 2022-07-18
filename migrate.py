import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent / "tests"))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproject.settings")
    from django.core.management import execute_from_command_line

    args = sys.argv + ["migrate"]
    execute_from_command_line(args)
