import datetime
import os
import subprocess
import textwrap
from dataclasses import dataclass

import httpx
import toml as tomllib
from packaging.version import Version

from . import githubref
from .releasefile import ReleasePreview, parse_release_file
from .utils import PATHS

REPO_SLUG = "nrbnlulu/strawberry-django-auth"

PROJECT_NAME = "gqlauth"
git_username = "GqlAuthBot"
git_email = "bot@no.reply"


def git(*args: str) -> None:
    return subprocess.run(["git", *args], check=False).check_returncode()


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
    current_commit = (
        subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    )
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
        msg = "No commit found"
        raise Exception(msg)

    prs = commit["associatedPullRequests"]["nodes"]

    if not prs:
        msg = "No PR was created for the last commit"
        raise Exception(msg)

    pr = prs[0]
    pr_number = pr["number"]
    pr_author_username = pr["author"]["login"]
    pr_author_fullname = pr["author"].get("name", "")
    return PRContributor(
        pr_number=pr_number,
        pr_author_fullname=pr_author_fullname,
        pr_author_username=pr_author_username,
    )


def get_contributor_details(contributor: PRContributor) -> str:
    return (
        f"Contributed by [{contributor.pr_author_fullname or contributor.pr_author_username}]"
        f"(https://github.com/{contributor.pr_author_username}) via [PR #{contributor.pr_number}]"
        f"(https://github.com/{REPO_SLUG}/pull/{contributor.pr_number}/)"
    )


def get_current_version() -> str:
    pyproject = tomllib.loads(PATHS.PYPROJECT_TOML.read_text(encoding="utf-8"))
    return pyproject["project"]["version"]


def bump_version(bump_string: str) -> None:
    current_version = Version(get_current_version())

    def semver_to_str(major: int, minor: int, patch: int) -> str:
        return f"{major}.{minor}.{patch}"

    match bump_string.lower():
        case "major":
            new_version = semver_to_str(current_version.major + 1, 0, 0)
        case "minor":
            new_version = semver_to_str(
                current_version.major, current_version.minor + 1, 0
            )
        case "patch":
            new_version = semver_to_str(
                current_version.major, current_version.minor, current_version.micro + 1
            )
        case _:
            msg = f"Unknown bump string: {bump_string}"
            raise ValueError(msg)
    pyproject = tomllib.loads(PATHS.PYPROJECT_TOML.read_text(encoding="utf-8"))
    pyproject["project"]["version"] = new_version
    PATHS.PYPROJECT_TOML.write_text(tomllib.dumps(pyproject), encoding="utf-8")


def pprint_release_change_log(
    release_preview: ReleasePreview, contrib_details: str
) -> str:
    current_changes = release_preview.changelog_no_header

    def is_first_or_last_line_empty(s: str) -> bool:
        return s.startswith("\n") or s.endswith("\n")

    while is_first_or_last_line_empty(current_changes):
        current_changes = current_changes.strip("\n")
    return f"{current_changes}\n\n{contrib_details}"


def update_change_log(current_changes: str, version: str) -> None:
    main_header = "CHANGELOG\n=========\n"

    this_header = textwrap.dedent(
        f"""{version} - {datetime.datetime.now(tz=datetime.UTC).date().isoformat()}\n--------------------\n""",
    )
    previous = PATHS.CHANGELOG.read_text(encoding="utf-8").strip(main_header)
    PATHS.CHANGELOG.write_text(
        textwrap.dedent(
            f"{main_header}{this_header}{current_changes}\n\n{previous}\n",
        ),
        encoding="utf-8",
    )


def main() -> None:
    os.chdir(PATHS.PROJECT_ROOT)
    release_file = parse_release_file(PATHS.RELEASE_FILE.read_text(encoding="utf-8"))
    bump_version(release_file.type.value)
    bumped_version = get_current_version()
    token = os.getenv("BOT_TOKEN")
    assert token
    current_contributor = get_last_commit_contributor(token=token)
    contributor_details = get_contributor_details(current_contributor)
    pretty_changes = pprint_release_change_log(release_file, contributor_details)
    update_change_log(pretty_changes, bumped_version)
    configure_git(git_username, git_email)

    git(
        "add",
        str(PATHS.PYPROJECT_TOML.resolve(True)),  # noqa: FBT003
        str(PATHS.CHANGELOG.resolve(True)),  # noqa: FBT003
    )
    # remove release file
    git("rm", str(PATHS.RELEASE_FILE))
    git("commit", "-m", f"Release {PROJECT_NAME}@{bumped_version}", "--no-verify")
    git("push", "origin", "HEAD")
    # GitHub release
    repo = githubref.get_repo(githubref.get_github_session(os.getenv("BOT_TOKEN", "")))
    release = repo.create_git_release(
        name=f"{PROJECT_NAME} {bumped_version}",
        tag=bumped_version,
        generate_release_notes=False,
        message=pretty_changes,
    )
    # publish python to GitHub
    subprocess.run(["uv", "build"], check=False)
    for file in PATHS.PROJECT_ROOT.glob("dist/*"):
        release.upload_asset(path=str(file))


if __name__ == "__main__":
    main()
