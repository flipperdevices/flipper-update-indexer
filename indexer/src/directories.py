import logging
import re
from fastapi import APIRouter
from .dirparser import parseDirectory
from .indextypes import *
from .settings import settings
from .indexer_github import indexerGithubConnect
from fastapi.responses import JSONResponse
from github import Repository


class DirectoryIndex:
    index_json: dict
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
                raise Exception(f"Cannot parse target for file {file}")
        self.target = target + "/" + jsonArch
        self.type = file_type


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
def directory_request(directory):
    try:
        return indexes.get(directory).index_json
    except Exception as e:
        raise e


@router.get("/{directory}/reindex")
def reindex_request(directory):
    try:
        return indexes.get(directory).reindexRequest()
    except Exception as e:
        raise e
