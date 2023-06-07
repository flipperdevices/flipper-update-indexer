import re
import hashlib
import logging
from pydantic import BaseModel
from github import Github, Repository
from typing import List


class VersionFile(BaseModel):
    url: str
    target: str
    type: str
    sha256: str


class Version(BaseModel):
    version: str
    changelog: str
    timestamp: int
    files: List[VersionFile] = []

    def add_file(self, file: VersionFile) -> None:
        self.files.append(file)


class Channel(BaseModel):
    id: str
    title: str
    description: str
    versions: List[Version] = []

    def add_version(self, version: Version) -> None:
        self.versions.append(version)


class Index(BaseModel):
    channels: List[Channel] = []

    def add_channel(self, channel: Channel) -> None:
        self.channels.append(channel)


class IndexerGithub:
    __repo: Repository.Repository = None
    __tags: List = []
    __releases: List = []
    __branches: List = []

    def login(self, token: str, repo_name: str, org_name: str) -> None:
        try:
            git = Github(token)
            org = git.get_organization(org_name)
            self.__repo = org.get_repo(repo_name)
        except Exception as e:
            logging.exception(e)
            raise e

    def __get_tags(self) -> None:
        try:
            github_tags = self.__repo.get_tags()
            self.__tags = [x.name for x in github_tags]
        except Exception as e:
            logging.exception(e)
            raise e

    def __get_releases(self) -> None:
        try:
            github_releases = self.__repo.get_releases()
            self.__releases = [x.title for x in github_releases]
        except Exception as e:
            logging.exception(e)
            raise e

    def __get_branches(self) -> None:
        try:
            github_branches = self.__repo.get_branches()
            self.__branches = [x.name for x in github_branches]
        except Exception as e:
            logging.exception(e)
            raise e

    def sync_info(self):
        self.__get_tags()
        self.__get_releases()
        self.__get_branches()

    """
        We need all stuff above (except login) for the delete_unlinked_directories function in repository.py
    """

    def is_branch_exist(self, branch: str) -> bool:
        return branch in self.__branches

    def is_release_exist(self, release: str) -> bool:
        return release in self.__releases

    def is_tag_exist(self, tag: str) -> bool:
        return tag in self.__tags

    def get_dev_version(self) -> Version:
        try:
            commits = self.__repo.get_commits()
            if commits.totalCount == 0:
                raise Exception(f"No comments found!")
            last_commit = commits[0]
            return Version(
                version=last_commit.sha[:8],
                changelog="Last commit: " + last_commit.commit.message,
                timestamp=int(last_commit.commit.author.date.timestamp()),
            )
        except Exception as e:
            logging.exception(e)
            raise e

    def get_release_version(self) -> Version:
        releases = self.__repo.get_releases()
        if releases.totalCount == 0:
            raise Exception(f"No releases found!")
        try:
            last_release = next(filter(lambda c: c.prerelease, releases))
            return Version(
                version=last_release.title,
                changelog=last_release.body,
                timestamp=int(last_release.created_at.timestamp()),
            )
        except StopIteration:
            return None

    def get_rc_version(self) -> Version:
        releases = self.__repo.get_releases()
        if releases.totalCount == 0:
            raise Exception(f"No release-candidates found!")
        try:
            last_release = next(filter(lambda c: not c.prerelease, releases))
            return Version(
                version=last_release.title,
                changelog=last_release.body,
                timestamp=int(last_release.created_at.timestamp()),
            )
        except StopIteration:
            return None


class FileParser(BaseModel):
    target: str = ""
    type: str = ""

    def getSHA256(self, filepath: str) -> str:
        with open(filepath, "rb") as file:
            file_bytes = file.read()
            sha256 = hashlib.sha256(file_bytes).hexdigest()
        return sha256

    def parse(self, filename: str) -> None:
        regex = re.compile(
            r"^flipper-z-(\w+)-(\w+)-([0-9.]+(-rc)?|(dev-\w+-\w+))\.(\w+)$"
        )
        match = regex.match(filename)
        if not match:
            raise Exception(f"Unknown file {filename}")
        self.target = match.group(1)
        self.type = match.group(2) + "_" + match.group(6)


class qFlipperFileParser(FileParser):
    def parse(self, filename: str) -> None:
        regex = re.compile(r"^(qFlipper\w*)(-.+)*-([0-9.a]+)(-rc\d+)?\.(\w+)$")
        match = regex.match(filename)
        if not match:
            return
        arch = match.group(2)
        extention = match.group(5)
        if extention == "dmg":
            target = "macos"
            file_type = "dmg"
        elif extention == "zip":
            target = "windows"
            file_type = "portable"
        elif extention == "AppImage":
            target = "linux"
            file_type = "AppImage"
        elif extention == "exe":
            target = "windows"
            file_type = "installer"
        else:
            raise Exception(f"Unknown file extention {extention}")
        if extention == "dmg":  # MacOS case
            jsonArch = "amd64"
        else:
            arch = arch.split("-")[1]
            if arch in ["64bit", "x86_64"]:
                jsonArch = "amd64"
            else:
                raise Exception(f"Cannot parse target")
        self.target = target + "/" + jsonArch
        self.type = file_type


class blackmagicFileParser(FileParser):
    def parse(self, filename: str) -> None:
        regex = re.compile(
            r"^blackmagic-firmware-(\w+)-(\w+)-([0-9.]+(-rc)?|(dev-\w+-\w+))\.(\w+)$"
        )
        match = regex.match(filename)
        if not match:
            raise Exception(f"Unknown file {filename}")
        self.target = match.group(1)
        self.type = match.group(2) + "_" + match.group(6)
