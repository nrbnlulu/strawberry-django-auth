from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import jinja2

try:
    from . import githubref, releasefile

except ImportError:
    import githubref
    import releasefile


template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=jinja2.select_autoescape(),
)

BOT_COMMENT_TEMPLATE = template_env.get_template("bot_comment.jinja.md")


@dataclass
class BotCommentContext:
    release_preview: releasefile.ReleasePreview | None = None


def render(context: BotCommentContext) -> str:
    return BOT_COMMENT_TEMPLATE.render(context=context)


def main() -> None:
    session = githubref.get_github_session(os.getenv("BOT_TOKEN", ""))
    pr = githubref.get_pr(session, int(os.getenv("PR_NUMBER", "")))
    preview = None
    try:
        preview = releasefile.get_release_preview(pr)
    except releasefile.InvalidReleaseFileError as exc:
        raise exc
    finally:
        content = render(
            BotCommentContext(preview),
        )
        githubref.create_or_update_bot_comment(pr, content)


if __name__ == "__main__":
    main()
