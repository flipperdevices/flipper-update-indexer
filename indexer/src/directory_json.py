from fastapi import APIRouter
import logging
from fastapi.responses import JSONResponse
from .settings import settings
import hashlib
from . import indexer_github
from .indextypes import Version, VersionFile, Channel, Index
import json
import re
import os

router = APIRouter()
directory_json = Index()

development_channel = Channel(
    "development",
    "Development Channel",
    "Latest builds, not yet tested by Flipper QA, be careful",
)
release_candidate_channel = Channel(
    "release-candidate",
    "Release Candidate Channel",
    "This is going to be released soon, undergoing QA tests now",
)
release_channel = Channel(
    "release", "Stable Release Channel", "Stable releases, tested by Flipper QA"
)


def getSHA256(filepath: str) -> str:
    with open(filepath, "rb") as file:
        file_bytes = file.read()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
    return sha256


def addFilesToVersion(version: Version, directory: str) -> Version:
    directory_path = os.path.join(settings.files_dir, directory)
    regex = re.compile(r"^flipper-z-(f7|any)-(\w+)-([a-zA-Z0-9-_.]+)\.(\w+)$")
    if not os.path.isdir(directory_path):
        raise Exception(f"Directory {directory} not found!")
    for cur in sorted(os.listdir(directory_path)):
        match = regex.match(cur)
        if match:
            version.add_file(
                VersionFile(
                    os.path.join(settings.base_url, directory, cur),
                    match.group(1),
                    match.group(2) + "_" + match.group(4),
                    getSHA256(os.path.join(directory_path, cur)),
                )
            )
    return version


def parseDevChannel(channel: Channel) -> Version:
    version = indexer_github.getDevDetails()
    version = addFilesToVersion(version, "dev")
    channel.add_version(version)
    return channel


def parseRelease(channel: Channel, isRC: bool) -> Version:
    version = indexer_github.getReleaseDetails(isRC)
    version = addFilesToVersion(version, version.version)
    channel.add_version(version)
    return channel


def parseChannel(channel: Channel) -> Channel:
    if channel == development_channel:
        channel = parseDevChannel(channel)
    elif channel == release_candidate_channel:
        channel = parseRelease(channel, True)
    elif channel == release_channel:
        channel = parseRelease(channel, False)
    return channel


def generate_index() -> None:
    global directory_json
    new_json = Index()
    try:
        new_json.add_channel(parseChannel(development_channel))
        new_json.add_channel(parseChannel(release_candidate_channel))
        new_json.add_channel(parseChannel(release_channel))
        directory_json = new_json
        logging.info("Reindex completed")
    except Exception as e:
        logging.error("Reindex failed")
        logging.exception(e)


@router.get("/directory.json")
async def directory():
    return JSONResponse(directory_json.__dict__)


@router.get("/reindex")
async def reindex():
    try:
        generate_index()
        return JSONResponse("ok")
    except Exception as e:
        return JSONResponse("fail")
