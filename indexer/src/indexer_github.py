from github import Github
from datetime import datetime, timedelta
from .settings import settings
from .indextypes import Version
import logging

def githubConnect(token: str, org: str, repo: str):
    try:
        git = Github(token)
        org = git.get_organization(org)
        code = org.get_repo(repo)
        return code
    except Exception as e:
        logging.exception(e)

__connect = githubConnect(settings.github_token, settings.github_org, settings.github_repo)


def getDevDetails() -> Version:
    since = datetime.now() - timedelta(days=10)
    commits = __connect.get_commits(since=since)
    last_commit = commits[0]
    version = Version(
        last_commit.sha[:8],
        "Last commit: " + last_commit.commit.message,
        int(last_commit.commit.author.date.strftime("%s")),
    )
    return version


def getReleaseDetails(isRC: bool) -> Version:
    releases = __connect.get_releases()
    for cur in releases:
        if cur.prerelease == isRC:
            last_release = cur
            break
    version = Version(
        last_release.title,
        last_release.body,
        int(last_release.created_at.strftime("%s")),
    )
    return version
