import itertools
import json
from typing import TypedDict

from typer import Typer

from . import bot_comment, checkrelease, release

app = Typer(name="management")


@app.command()
def check_release() -> None:
    checkrelease.main()


@app.command(name="release")
def release_command() -> None:
    release.main()


@app.command(name="bot_comment")
def bot_comment_command() -> None:
    bot_comment.main()


class TestedNode(TypedDict):
    name: str
    cmd: str
    workdir: str


@app.command(name="test_matrix")
def test_matrix_command() -> None:
    from mainserver.tools.constants import PATHS  # noqa: PLC0415

    def default_test_command(*flags: str) -> str:
        return f"uv run pytest {" ".join(list(flags))} --cov=src --cov-report=xml"

    micro_services = [
        src.parent for src in PATHS.MICROSERVICES.glob("**/pyproject.toml")
    ]
    libs = [
        src.parent
        for src in PATHS.LIBS.glob("**/pyproject.toml")
        if src.parent.name != "devdeps"
    ]
    domains: dict[str, TestedNode] = {}
    domains.update(
        {
            node.name: {
                "name": node.name,
                "cmd": default_test_command(),
                "workdir": str(node),
            }
            for node in itertools.chain(micro_services, libs)
        }
    )

    milesight = domains["milesight"]
    milesight["cmd"] = default_test_command('-m "not needs_active_nvr"')

    onvif = domains["onvif"]
    onvif["cmd"] = default_test_command('-m "not integration_tests"')

    matrix = json.dumps({"tested_domain": list(domains.values())})
    with open("GITHUB_OUTPUT", "a") as fh:  # noqa: PLW1514, PTH123
        fh.write(matrix)
    print(matrix)  # noqa: T201


if __name__ == "__main__":
    app()
