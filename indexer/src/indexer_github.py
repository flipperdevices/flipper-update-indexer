import logging
from github import Github, Repository, Branch
from .models import Version


def is_branch_exist(repository: Repository.Repository, branch: str) -> bool:
    try:
        repository.get_branch(branch)
    except Exception:
        return False
    return True


def is_release_exist(repository: Repository.Repository, release: str) -> bool:
    try:
        repository.get_release(release)
    except Exception:
        return False
    return True


def get_github_repository(token: str, org_name: str, repo_name: str) -> Repository:
    """
    A method to get a GitHub repository by name
    Args:
        token: Git token for authorization
        org_name: Organization name
        repo_name: Repository name

    Returns:
        Repository object
    """
    try:
        git = Github(token)
        org = git.get_organization(org_name)
        code = org.get_repo(repo_name)
        return code
    except Exception as e:
        logging.exception(e)
        raise e


def get_dev_version(repository: Repository.Repository) -> Version:
    """
    A method to retrieve the last commit in a
    dev branch and build a model from it
    Args:
        repository: Repo object

    Returns:
        Commit model
    """
    commits = repository.get_commits()
    if commits.totalCount == 0:
        raise Exception(f"No comments found!")
    last_commit = commits[0]
    return Version(
        version=last_commit.sha[:8],
        changelog="Last commit: " + last_commit.commit.message,
        timestamp=int(last_commit.commit.author.date.timestamp()),
    )


def get_release_version(repository: Repository.Repository) -> Version:
    """
    A method to retrieve the last commit of release
    and build a model from it
    Args:
        repository: Repo object

    Returns:
        Commit model
    """
    releases = repository.get_releases()
    if releases.totalCount == 0:
        raise Exception(f"No releases found!")
    last_release = next(filter(lambda c: c.prerelease, repository.get_releases()))
    return Version(
        version=last_release.title,
        changelog=last_release.body,
        timestamp=int(last_release.created_at.timestamp()),
    )


def get_rc_version(repository: Repository.Repository) -> Version:
    """
    A method to retrieve the last commit of rc
    and build a model from it
    Args:
        repository: Repo object

    Returns:
        Commit model
    """
    releases = repository.get_releases()
    if releases.totalCount == 0:
        raise Exception(f"No release-candidates found!")
    last_release = next(filter(lambda c: not c.prerelease, repository.get_releases()))
    return Version(
        version=last_release.title,
        changelog=last_release.body,
        timestamp=int(last_release.created_at.timestamp()),
    )
