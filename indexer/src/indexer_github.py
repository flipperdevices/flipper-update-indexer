from github import Github
from datetime import datetime, timedelta
from .settings import settings
from .indextypes import Version
import logging


def githubConnect(token: str, org_name: str, repo_name: str):
    try:
        git = Github(token)
        org = git.get_organization(org_name)
        code = org.get_repo(repo_name)
        return code
    except Exception as e:
        logging.exception(e)


__firmware_github_connect = githubConnect(
    settings.firmware_github_token, settings.github_org, settings.firmware_github_repo
)

__qFlipper_github_connect = githubConnect(
    settings.qFlipper_github_token, settings.github_org, settings.qFlipper_github_repo
)


def getDevDetails(directory: str) -> Version:
    if directory == "firmware":
        connect = __firmware_github_connect
    elif directory == "qFlipper":
        connect = __qFlipper_github_connect
    else:
        raise Exception(f"Unknown directory to parse")
    since = datetime.now() - timedelta(days=10)
    commits = connect.get_commits(since=since)
    last_commit = commits[0]
    version = Version(
        version=last_commit.sha[:8],
        changelog="Last commit: " + last_commit.commit.message,
        timestamp=int(last_commit.commit.author.date.strftime("%s")),
    )
    return version


def getReleaseDetails(directory: str, isRC: bool) -> Version:
    if directory == "firmware":
        connect = __firmware_github_connect
    elif directory == "qFlipper":
        connect = __qFlipper_github_connect
    else:
        raise Exception(f"Unknown directory to parse")
    releases = connect.get_releases()
    for cur in releases:
        if cur.prerelease == isRC:
            last_release = cur
            break
    version = Version(
        version=last_release.title,
        changelog=last_release.body,
        timestamp=int(last_release.created_at.strftime("%s")),
    )
    return version
