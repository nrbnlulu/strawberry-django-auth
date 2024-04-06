import datetime
import os
import re
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path

import httpx
import tomllib

from . import githubref
from .releasefile import ReleasePreview, parse_release_file
from .utils import PATHS

REPO_SLUG = "nrbnlulu/strawberry-django-auth"

PROJECT_NAME = "gqlauth"
git_username = "GqlAuthBot"
git_email = "bot@no.reply"


def git(*args: str):
    return subprocess.run(["git", *args]).check_returncode()


def configure_git(username: str, email: str) -> None:
    git("config", "user.name", username)
    git("config", "user.email", email)


@dataclass
class PRContributor:
    pr_number: int
    pr_author_username: str
    pr_author_fullname: str


def get_last_commit_contributor(token: str) -> PRContributor:
    org, repo = REPO_SLUG.split("/")
    current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    response = httpx.post(
        "https://api.github.com/graphql",
        json={
            "query": """query Contributor(
                $owner: String!
                $name: String!
                $commit: GitObjectID!
            ) {
                repository(owner: $owner, name: $name) {
                    object(oid: $commit) {
                        __typename
                        ... on Commit {
                            associatedPullRequests(first: 1) {
                                nodes {
                                    number
                                    author {
                                        __typename
                                        login
                                        ... on User {
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }""",
            "variables": {"owner": org, "name": repo, "commit": current_commit},
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    payload = response.json()
    commit = payload["data"]["repository"]["object"]

    if not commit:
        raise Exception("No commit found")

    prs = commit["associatedPullRequests"]["nodes"]

    if not prs:
        raise Exception("No PR was created for the last commit")

    pr = prs[0]
    pr_number = pr["number"]
    pr_author_username = pr["author"]["login"]
    pr_author_fullname = pr["author"].get("name", "")
    return PRContributor(
        pr_number=pr_number,
        pr_author_fullname=pr_author_fullname,
        pr_author_username=pr_author_username,
    )


INIT_FILE = PATHS.PROJECT_ROOT / "__init__.py"


def update_python_versions(version: str) -> None:
    assert INIT_FILE.exists()
    pattern = r'__version__: str = "([\d.]+)"'

    def replace__version__(file: Path) -> None:
        def ver_repl(match: re.Match) -> str:
            return match.group(0).replace(match.group(1), version)

        replaced = re.sub(pattern, ver_repl, file.read_text(), count=1)
        file.write_text(replaced, "UTF-8")

    replace__version__(INIT_FILE)


def get_contributor_details(contributor: PRContributor) -> str:
    return (
        f"Contributed by [{contributor.pr_author_fullname or contributor.pr_author_username}]"
        f"(https://github.com/{contributor.pr_author_username}) via [PR #{contributor.pr_number}]"
        f"(https://github.com/{REPO_SLUG}/pull/{contributor.pr_number}/)"
    )


def get_current_version() -> str:
    pyproject = tomllib.loads(PATHS.PYPROJECT_TOML.read_text(encoding="utf-8"))
    return pyproject["tool"]["poetry"]["version"]


def bump_version(bump_string: str) -> None:
    subprocess.run(["poetry", "version", bump_string])


def pprint_release_change_log(release_preview: ReleasePreview, contrib_details: str) -> str:
    current_changes = "".join(release_preview.changelog.splitlines()[1:])  # remove release type

    def is_first_or_last_line_empty(s: str) -> bool:
        return s.startswith("\n") or s.endswith("\n")

    while is_first_or_last_line_empty(current_changes):
        current_changes = current_changes.strip("\n")
    return f"{current_changes}\n\n{contrib_details}"


def update_change_log(current_changes: str, version: str) -> None:
    main_header = "CHANGELOG\n=========\n"

    this_header = textwrap.dedent(
        f"""{version} - {datetime.datetime.now(tz=datetime.timezone.utc).date().isoformat()}\n--------------------\n""",
    )
    previous = PATHS.CHANGELOG.read_text(encoding="utf-8").strip(main_header)
    PATHS.CHANGELOG.write_text(
        textwrap.dedent(
            f"{main_header}" f"{this_header}" f"{current_changes}\n\n" f"{previous}",
        ),
        encoding="utf-8",
    )


def main() -> None:
    os.chdir(PATHS.PROJECT_ROOT)
    release_file = parse_release_file(PATHS.RELEASE_FILE.read_text(encoding="utf-8"))
    bump_version(release_file.type.value)
    bumped_version = get_current_version()
    current_contributor = get_last_commit_contributor(
        os.getenv("BOT_TOKEN", None),
    )
    contributor_details = get_contributor_details(current_contributor)
    pretty_changes = pprint_release_change_log(release_file, contributor_details)
    update_change_log(pretty_changes, bumped_version)
    update_python_versions(bumped_version)
    configure_git(git_username, git_email)
    git(
        "add",
        str(PATHS.ROOT_CMAKE),
        str(INIT_FILE),
        str(PATHS.PYPROJECT_TOML.resolve(True)),
        str(PATHS.CHANGELOG.resolve(True)),
    )
    # remove release file
    git("rm", str(PATHS.RELEASE_FILE))
    git("commit", "-m", f"Release {PROJECT_NAME}@{bumped_version}", "--no-verify")
    git("push", "origin", "HEAD")
    # GitHub release
    repo = githubref.get_repo(githubref.get_github_session())
    release = repo.create_git_release(
        name=f"{PROJECT_NAME} {bumped_version}",
        tag=bumped_version,
        generate_release_notes=False,
        message=pretty_changes,
    )
    # publish python to GitHub
    subprocess.run(["poetry", "build"])
    for file in PATHS.PROJECT_ROOT.glob("dist/*"):
        release.upload_asset(path=str(file))


if __name__ == "__main__":
    main()
