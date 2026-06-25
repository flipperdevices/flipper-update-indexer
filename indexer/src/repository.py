import logging

from .parsers import parse_github_channels
from .models import *
from .settings import settings
from .storage import storage
from .models import (
    qFlipperFileParser,
    blackmagicFileParser,
    vgmFileParser,
    busybarFileParser,
    flipperOneMcuFileParser,
)


class RepositoryIndex:
    index: dict

    def __init__(
        self,
        directory: str,
        github_token: str,
        github_repo: str,
        github_org: str,
        file_parser: FileParser = FileParser,
    ):
        self.index = Index().dict()
        self.directory = directory
        self.file_parser = file_parser
        self._github_token = github_token
        self._github_repo = github_repo
        self._github_org = github_org
        self._indexer_github = None

    @property
    def indexer_github(self) -> IndexerGithub:
        # Login lazily so the service can import and start without valid GitHub
        # credentials (local/dev): the GitHub API is only hit on reindex.
        if self._indexer_github is None:
            github = IndexerGithub()
            github.login(self._github_token, self._github_repo, self._github_org)
            self._indexer_github = github
        return self._indexer_github

    def delete_empty_directories(self):
        """
        A method for cleaning directories that are empty
        Returns:
            Nothing
        """
        for sub_dir in storage.list_dirs(self.directory):
            if storage.list_files(self.directory, sub_dir) or storage.list_dirs(
                self.directory, sub_dir
            ):
                continue
            storage.delete_tree(self.directory, sub_dir)
            logging.info(f"Deleting {self.directory}/{sub_dir}")

    def delete_unlinked_directories(self):
        """
        A method for cleaning directories that do not match
        branches/releases in the repository
        Args:
            Nothing

        Returns:
            Nothing
        """
        self.indexer_github.sync_info()
        for relative_dir, files in storage.walk(self.directory):
            # skip the main directory itself
            if relative_dir in (".", ""):
                continue

            # skip .DS_store files
            if len(files) == 1 and files[0].startswith("."):
                continue

            if self.indexer_github.is_release_exist(relative_dir):
                continue
            if self.indexer_github.is_tag_exist(relative_dir):
                continue
            if self.indexer_github.is_branch_exist(relative_dir):
                continue
            storage.delete_tree(self.directory, relative_dir)
            logging.info(f"Deleting {self.directory}/{relative_dir}")

    def reindex(self):
        """
        Method for starting reindexing. We get three channels - dev, release,
        rc from the main repository in the git. We run through all 3 channels,
        each channel has different versions inside. We create models for all
        versions and stuff them with the path to the artifacts.

        At the end of reindexing, all unnecessary branches and
        empty directories are cleared

        Returns:
            Nothing
        """
        try:
            self.index = parse_github_channels(
                self.directory, self.file_parser, self.indexer_github
            )
            logging.info(f"{self.directory} reindex OK")
            self.delete_unlinked_directories()
            self.delete_empty_directories()
        except Exception as e:
            logging.error(f"{self.directory} reindex failed")
            logging.exception(e)
            raise e

    def get_file_from_latest_version(
        self: str, channel: str, target: str, file_type: str
    ) -> str:
        """
        A method to get a file in the latest version of the
        current directory by its target and type
        Args:
            channel: Channel type (release, rc, dev)
            target: Operating System (linux, mac, win)
            file_type: File Type

        Returns:
            String URL of file`s location
        """
        target = target.replace("-", "/")
        try:
            channels = self.index["channels"]
            current_channel = next(
                filter(lambda c: c.get("id") == channel, channels), None
            )

            if current_channel is None:
                valueerr_msg = f"Channel `{channel}` not found!"
                logging.exception(valueerr_msg)
                raise ValueError(valueerr_msg)

            latest_version = current_channel.get("versions")[0]
            latest_version_file = next(
                filter(
                    lambda c: c.get("target") == target and c.get("type") == file_type,
                    latest_version.get("files"),
                )
            )
            return latest_version_file.get("url")
        except Exception as e:
            logging.exception(e)
            raise e


# Catalog of every directory the upstream indexer can build. Only directories
# listed in settings.enabled_directories are activated, so a Busy-only instance
# runs just "busybar-firmware" without needing the other repositories' tokens.
_directory_catalog = {
    "firmware": (
        settings.firmware_github_token,
        settings.firmware_github_repo,
        FileParser,
    ),
    "qFlipper": (
        settings.qFlipper_github_token,
        settings.qFlipper_github_repo,
        qFlipperFileParser,
    ),
    "blackmagic-firmware": (
        settings.blackmagic_github_token,
        settings.blackmagic_github_repo,
        blackmagicFileParser,
    ),
    "vgm-firmware": (
        settings.vgm_github_token,
        settings.vgm_github_repo,
        vgmFileParser,
    ),
    "busybar-firmware": (
        settings.busybar_github_token,
        settings.busybar_github_repo,
        busybarFileParser,
    ),
    "flipper-one-mcu": (
        settings.flipper_one_mcu_github_token,
        settings.flipper_one_mcu_github_repo,
        flipperOneMcuFileParser,
    ),
}

indexes = {
    directory: RepositoryIndex(
        directory=directory,
        github_token=github_token,
        github_repo=github_repo,
        github_org=settings.github_org,
        file_parser=file_parser,
    )
    for directory, (
        github_token,
        github_repo,
        file_parser,
    ) in _directory_catalog.items()
    if directory in settings.enabled_directories
}

raw_file_upload_directories = list(settings.raw_upload_directories)
