import logging
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from github import Repository
from .dirparser import parseDirectory
from .indextypes import *
from .settings import settings
from .indexer_github import indexerGithubConnect
from .extrafileparsers import qFlipperFileParser


class DirectoryIndex:
    index_json: dict = Index().dict()
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
        self.index_json = Index().dict()
        self.directory = directory
        self.github_token = github_token
        self.github_repo = github_repo
        self.github_org = github_org
        self.file_parser = file_parser

    def reindex(self):
        try:
            github_connect = indexerGithubConnect(
                self.github_token, self.github_org, self.github_repo
            )
            self.index_json = parseDirectory(
                self.directory, self.file_parser, github_connect
            )
            logging.info(f"{self.directory} reindex complited")
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


@router.get("/{directory}/reindex")
async def reindex_request(directory):
    index = indexes.get(directory)
    if index:
        async with lock:
            return indexes.get(directory).reindexRequest()
    return JSONResponse("Not found", status_code=404)
