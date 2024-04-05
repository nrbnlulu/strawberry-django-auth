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


if __name__ == "__main__":
    app()
