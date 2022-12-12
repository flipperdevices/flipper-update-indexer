from github import Github
from datetime import datetime, timedelta
from .settings import settings

git = Github(settings.github_token)
org = git.get_organization(settings.github_org)
code = org.get_repo(settings.github_repo)


def getDevDetails() -> dict:
    since = datetime.now() - timedelta(days=1)
    commits = code.get_commits(since=since)
    last_commit = commits[0]
    details = {
        "version": last_commit.sha[:8],
        "changelog": "Last commit: " + last_commit.commit.message,
        "timestamp": int(last_commit.commit.author.date.strftime("%s")),
    }
    return details


def getReleaseDetails(isRC: bool) -> dict:
    releases = code.get_releases()
    for cur in releases:
        if cur.prerelease == isRC:
            last_release = cur
            break
    details = {
        "version": last_release.title,
        "changelog": last_release.body,
        "timestamp": int(last_release.created_at.strftime("%s")),
    }
    return details
