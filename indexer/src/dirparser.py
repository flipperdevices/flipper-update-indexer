import os
import logging
import copy
from github import Repository
from .indextypes import *
from . import indexer_github
from .settings import settings


def checkDirectoryExist(directory: str) -> None:
    if not os.path.isdir(directory):
        raise Exception(f"Directory {directory} not found!")


def addFilesToVersion(
    version: Version, file_parser: FileParser, main_dir: str, sub_dir: str
) -> Version:
    directory_path = os.path.join(settings.files_dir, main_dir, sub_dir)
    checkDirectoryExist(directory_path)
    for cur in sorted(os.listdir(directory_path)):
        parsed_file = file_parser()
        parsed_file.parse(cur)
        version.add_file(
            VersionFile(
                url=os.path.join(settings.base_url, main_dir, sub_dir, cur),
                target=parsed_file.target,
                type=parsed_file.type,
                sha256=parsed_file.getSHA256(os.path.join(directory_path, cur)),
            )
        )
    return version


def parseDevChannel(
    channel: Channel,
    directory: str,
    file_parser: FileParser,
    github_connect: Repository.Repository,
) -> Channel:
    version = indexer_github.getDevDetails(github_connect, directory)
    version = addFilesToVersion(version, file_parser, directory, "dev")
    channel.add_version(version)
    return channel


def parseReleaseChannel(
    channel: Channel,
    directory: str,
    file_parser: FileParser,
    github_connect: Repository.Repository,
    isRC: bool,
) -> Channel:
    version = indexer_github.getReleaseDetails(github_connect, directory, isRC)
    version = addFilesToVersion(version, file_parser, directory, version.version)
    channel.add_version(version)
    return channel


def parseDirectory(
    directory: str, file_parser: FileParser, github_connect: Repository.Repository
) -> dict:
    json = Index()
    json.add_channel(
        parseDevChannel(
            copy.deepcopy(development_channel), directory, file_parser, github_connect
        )
    )
    json.add_channel(
        parseReleaseChannel(
            copy.deepcopy(release_candidate_channel),
            directory,
            file_parser,
            github_connect,
            isRC=True,
        )
    )
    json.add_channel(
        parseReleaseChannel(
            copy.deepcopy(release_channel),
            directory,
            file_parser,
            github_connect,
            isRC=False,
        )
    )
    return json.dict()
