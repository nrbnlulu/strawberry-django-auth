from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository


def get_github_session(token: str) -> Github:
    return Github(token)


def get_repo(g: Github) -> Repository:
    return g.get_repo("nrbnlulu/strawberry-django-auth")


def get_pr(g: Github, num: int) -> PullRequest:
    return get_repo(g).get_pull(num)


def create_or_update_bot_comment(pr: PullRequest, content: str) -> None:
    for cm in pr.get_issue_comments():
        if "878ae1db-766f-49c7-a1a8-59f7be1fee8f" in cm.body:
            cm.edit(content)
            return

    pr.create_issue_comment(content)
