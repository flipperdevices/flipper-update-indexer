import os
import shutil
import logging
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from github import Repository

from .parsers import parse_github_channels
from .models import *
from .settings import settings
from .indexer_github import get_github_repository, is_branch_exist, is_release_exist
from .models import qFlipperFileParser


class DirectoryIndex:

    index: dict = Index().dict()

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
        self.github_token = github_token
        self.github_repo = github_repo
        self.github_org = github_org
        self.file_parser = file_parser

    def delete_empty_directories(self):
        """
        A method for cleaning directories that are empty
        Returns:
            Nothing
        """
        main_dir = os.path.join(settings.files_dir, self.directory)
        for cur in os.listdir(main_dir):
            cur_dir = os.path.join(main_dir, cur)
            dir_content = os.listdir(cur_dir)
            if len(dir_content) > 0:
                continue
            shutil.rmtree(cur_dir)
            logging.info(f"Deleting {cur_dir}")

    def delete_unlinked_directories(self, repository: Repository.Repository):
        """
        A method for cleaning directories that do not match
        branches/releases in the repository
        Args:
            repository: Repository model

        Returns:
            Nothing
        """
        main_dir = os.path.join(settings.files_dir, self.directory)
        for root, dirs, files in os.walk(main_dir):
            if len(files) == 0:
                continue
            cur_dir = root.split(main_dir + "/")[1]
            if is_branch_exist(repository, cur_dir):
                continue
            if is_release_exist(repository, cur_dir):
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
            repository = get_github_repository(
                self.github_token, self.github_org, self.github_repo
            )
            self.index = parse_github_channels(
                self.directory, self.file_parser, repository
            )
            logging.info(f"{self.directory} reindex complited")
            # self.delete_unlinked_directories(repository)
            # self.delete_empty_directories()
        except Exception as e:
            logging.error(f"{self.directory} reindex failed")
            logging.exception(e)
            raise e

    def get_file_from_latest_version(self: str, channel: str, target: str, file_type: str) -> str:
        """
        A method to get a file in the latest version of the
        current directory by its target and type
        Args:
            channel: Channel type (release, rc, dev)
            target: Operation System (linux, mac, win)
            file_type: File Type

        Returns:
            String URL of file`s location
        """
        target = target.replace("-", "/")
        try:
            channels = self.index["channels"]
            current_channel = next(filter(lambda c: c.get("id") == channel, channels))
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


router = APIRouter()
lock = asyncio.Lock()


indexes = {
    "firmware": DirectoryIndex(
        directory="firmware",
        github_token=settings.firmware_github_token,
        github_repo=settings.firmware_github_repo,
        github_org=settings.github_org,
    ),
    "qFlipper": DirectoryIndex(
        directory="qFlipper",
        github_token=settings.qFlipper_github_token,
        github_repo=settings.qFlipper_github_repo,
        github_org=settings.github_org,
        file_parser=qFlipperFileParser,
    ),
}


@router.get("/{directory}/directory.json")
async def directory_request(directory):
    """
    Method for obtaining indices
    Args:
        directory: Repository name

    Returns:
        Indices in json
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    return indexes.get(directory).index


@router.get(
    "/{directory}/{channel}/{target}/{type}",
    response_class=RedirectResponse,
    status_code=302,
)
async def latest_request(directory, channel, target, file_type):
    """
    A method for retrieving a file from the repository
    of a specific version
    Args:
        directory: Repository name
        channel: Channel type (release, rc, dev)
        target: Operation System (linux, mac, win)
        file_type: File Type

    Returns:
        Artifact file
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    index = indexes.get(directory)
    if len(index.index["channels"]) == 0:
        return JSONResponse("No channels found!", status_code=404)
    try:
        return index.get_file_from_latest_version(channel, target, file_type)
    except Exception as e:
        return JSONResponse(e, status_code=404)


@router.post("/{directory}/reindex")
async def reindex_request(directory):
    """
    Method for starting reindexing
    Args:
        directory: Repository name

    Returns:
        Reindex status
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    async with lock:
        try:
            indexes.get(directory).reindex()
            return JSONResponse("Reindexing is done!")
        except Exception as e:
            logging.exception(e)
            return JSONResponse("Reindexing is failed!", status_code=500)
