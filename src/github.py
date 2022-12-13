from github import Github
from datetime import datetime, timedelta
from .settings import settings
from .types import Version

git = Github(settings.github_token)
org = git.get_organization(settings.github_org)
code = org.get_repo(settings.github_repo)


def getDevDetails() -> Version:
    since = datetime.now() - timedelta(days=1)
    commits = code.get_commits(since=since)
    last_commit = commits[0]
    version = Version(
        last_commit.sha[:8],
        "Last commit: " + last_commit.commit.message,
        int(last_commit.commit.author.date.strftime("%s")),
    )
    return version


def getReleaseDetails(isRC: bool) -> Version:
    releases = code.get_releases()
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
