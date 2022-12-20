from github import Github, Repository
from datetime import datetime, timedelta
from .settings import settings
from .indextypes import Version
import logging


def indexerGithubConnect(token: str, org_name: str, repo_name: str):
    try:
        git = Github(token)
        org = git.get_organization(org_name)
        code = org.get_repo(repo_name)
        return code
    except Exception as e:
        logging.exception(e)
        raise e


def getDevDetails(connect: Repository.Repository, isRC: bool) -> Version:
    since = datetime.now() - timedelta(days=10)
    commits = connect.get_commits(since=since)
    last_commit = commits[0]
    return Version(
        version=last_commit.sha[:8],
        changelog="Last commit: " + last_commit.commit.message,
        timestamp=int(last_commit.commit.author.date.timestamp()),
    )


def getReleaseDetails(
    connect: Repository.Repository, directory: str, isRC: bool
) -> Version:
    releases = connect.get_releases()
    last_release = next(filter(lambda c: c.prerelease == isRC, connect.get_releases()))
    for cur in releases:
        if cur.prerelease == isRC:
            last_release = cur
            break
    return Version(
        version=last_release.title,
        changelog=last_release.body,
        timestamp=int(last_release.created_at.timestamp()),
    )
