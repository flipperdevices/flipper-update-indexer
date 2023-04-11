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
    directory: str
    github_token: str
    github_repo: str
    github_org: str
    file_parser: FileParser

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

    def deleteEmptyDirectories(self):
        main_dir = os.path.join(settings.files_dir, self.directory)
        for cur in os.listdir(main_dir):
            cur_dir = os.path.join(main_dir, cur)
            dir_content = os.listdir(cur_dir)
            if not len(dir_content):
                shutil.rmtree(cur_dir)
                logging.info(f"Deleting {cur_dir}")

    def deleteUnlinkedDirectories(self, github_connect: Repository.Repository):
        main_dir = os.path.join(settings.files_dir, self.directory)
        for root, dirs, files in os.walk(main_dir):
            if not len(files):
                continue
            cur_dir = root.split(main_dir + "/")[1]
            if not is_branch_exist(github_connect, cur_dir):
                if not is_release_exist(github_connect, cur_dir):
                    shutil.rmtree(os.path.join(main_dir, cur_dir))
                    logging.info(f"Deleting {cur_dir}")

    def reindex(self):
        try:
            repository = get_github_repository(
                self.github_token, self.github_org, self.github_repo
            )
            self.index = parse_github_channels(
                self.directory, self.file_parser, repository
            )
            logging.info(f"{self.directory} reindex complited")
            self.deleteUnlinkedDirectories(repository)
            self.deleteEmptyDirectories()
        except Exception as e:
            logging.error(f"{self.directory} reindex faied")
            logging.exception(e)
            raise e

    def reindexRequest(self):
        try:
            self.reindex()
            return JSONResponse("ok")
        except Exception as e:
            logging.exception(e)
            return JSONResponse("fail", status_code=500)

    def get_file_from_latest_version(self: str, channel: str, target: str, file_type: str) -> str:
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
            return JSONResponse("Not found", status_code=404)


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
    index = indexes.get(directory)
    if index:
        return indexes.get(directory).index_json
    return JSONResponse("Not found", status_code=404)


@router.get(
    "/{directory}/{channel}/{target}/{type}",
    response_class=RedirectResponse,
    status_code=302,
)
async def latest_request(directory, channel, target, file_type):
    index = indexes.get(directory)
    if index:
        if len(index.index_json["channels"]) > 1:
            return index.get_file_from_latest_version(channel, target, file_type)
    return JSONResponse("Not found", status_code=404)


@router.get("/{directory}/reindex")
async def reindex_request(directory):
    index = indexes.get(directory)
    if index:
        async with lock:
            return indexes.get(directory).reindexRequest()
    return JSONResponse("Not found", status_code=404)
