import os
import shutil
import logging

from .parsers import parse_github_channels
from .models import *
from .settings import settings
from .models import qFlipperFileParser, blackmagicFileParser


class RepositoryIndex:
    index: dict
    indexer_github: IndexerGithub

    def __init__(
        self,
        directory: str,
        github_token: str,
        github_repo: str,
        github_org: str,
        file_parser: FileParser = FileParser,
    ):
        self.index = Index().dict()
        self.indexer_github = IndexerGithub()
        self.indexer_github.login(github_token, github_repo, github_org)
        self.directory = directory
        self.file_parser = file_parser

    def delete_empty_directories(self):
        """
        A method for cleaning directories that are empty
        Returns:
            Nothing
        """
        main_dir = os.path.join(settings.files_dir, self.directory)
        for cur in os.listdir(main_dir):
            if cur.startswith("."):
                continue
            cur_dir = os.path.join(main_dir, cur)
            dir_content = os.listdir(cur_dir)
            if len(dir_content) > 0:
                continue
            shutil.rmtree(cur_dir)
            logging.info(f"Deleting {cur_dir}")

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
        main_dir = os.path.join(settings.files_dir, self.directory)
        for root, dirs, files in os.walk(main_dir):
            if len(files) == 0:
                continue
            # skip .DS_store files
            if len(files) == 1 and files[0].startswith("."):
                continue
            cur_dir = root.split(main_dir + "/")[1]
            if self.indexer_github.is_release_exist(cur_dir):
                continue
            if self.indexer_github.is_tag_exist(cur_dir):
                continue
            if self.indexer_github.is_branch_exist(cur_dir):
                continue
            shutil.rmtree(os.path.join(main_dir, cur_dir))
            logging.info(f"Deleting {cur_dir}")

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
            current_channel = next(filter(lambda c: c.get("id") == channel, channels), None)

            if current_channel is None:
                raise ValueError(f'Channel `{channel}` not found!')

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


indexes = {
    "firmware": RepositoryIndex(
        directory="firmware",
        github_token=settings.firmware_github_token,
        github_repo=settings.firmware_github_repo,
        github_org=settings.github_org,
    ),
    "qFlipper": RepositoryIndex(
        directory="qFlipper",
        github_token=settings.qFlipper_github_token,
        github_repo=settings.qFlipper_github_repo,
        github_org=settings.github_org,
        file_parser=qFlipperFileParser,
    ),
    "blackmagic-firmware": RepositoryIndex(
        directory="blackmagic-firmware",
        github_token=settings.blackmagic_github_token,
        github_repo=settings.blackmagic_github_repo,
        github_org=settings.github_org,
        file_parser=blackmagicFileParser,
    ),
}
