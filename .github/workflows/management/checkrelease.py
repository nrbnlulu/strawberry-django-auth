import os

from .releasefile import parse_release_file
from .utils import PATHS


def main() -> None:
    with open(os.environ["GITHUB_OUTPUT"], "w") as f:  # noqa: PTH123
        if not PATHS.RELEASE_FILE.exists():
            f.write("status=Release file doesn't exist")
        else:
            parse_release_file(PATHS.RELEASE_FILE.read_text("utf-8"))
            f.write(f"status={''}")


if __name__ == "__main__":
    main()
