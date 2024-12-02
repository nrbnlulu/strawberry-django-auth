from pathlib import Path


class PATHS:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    PYPROJECT_TOML = PROJECT_ROOT / "pyproject.toml"
    CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
    RELEASE_FILE = PROJECT_ROOT / "RELEASE.md"
