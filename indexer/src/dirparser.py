import os
import re
import hashlib
import logging
import copy
from .indextypes import *
from . import indexer_github
from .settings import settings


def getSHA256(filepath: str) -> str:
    with open(filepath, "rb") as file:
        file_bytes = file.read()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
    return sha256


def checkDirectoryExist(directory: str) -> None:
    if not os.path.isdir(directory):
        raise Exception(f"Directory {directory} not found!")


def qFlipperParseTarget(target: str, match: re.Match, file: str) -> str:
    arch = match.group(2)
    extention = match.group(5)
    if extention == "dmg":  # MacOS case
        jsonArch = "amd64"
    else:
        arch = arch.split("-")[1]
        if arch in ["64bit", "x86_64"]:
            jsonArch = "amd64"
        else:
            raise Exception(f"Cannot parse target for file {file}")
    target = target + "/" + jsonArch
    return target


def qFlipperParseFile(
    version: Version, match: re.Match, url: str, sha256: str, file: str
) -> Version:
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
    target = qFlipperParseTarget(target, match, file)
    version.add_file(VersionFile(url=url, target=target, type=file_type, sha256=sha256))
    return version


def qFlipperAddFilesToVersion(version: Version, main_dir: str, sub_dir: str) -> Version:
    directory_path = os.path.join(settings.files_dir, main_dir, sub_dir)
    regex = re.compile(r"^(qFlipper\w*)(-.+)*-([0-9.a]+)(-rc\d+)?\.(\w+)$")
    checkDirectoryExist(directory_path)
    for cur in sorted(os.listdir(directory_path)):
        match = regex.match(cur)
        if match:
            url = os.path.join(settings.base_url, main_dir, sub_dir, cur)
            sha256 = getSHA256(os.path.join(directory_path, cur))
            try:
                version = qFlipperParseFile(version, match, url, sha256, cur)
            except Exception as e:
                logging.exception(e)
    return version


def firmwareAddFilesToVersion(version: Version, main_dir: str, sub_dir: str) -> Version:
    directory_path = os.path.join(settings.files_dir, main_dir, sub_dir)
    regex = re.compile(r"^flipper-z-(\w+)-(\w+)-([a-zA-Z0-9-_.]+)\.(\w+)$")
    checkDirectoryExist(directory_path)
    for cur in sorted(os.listdir(directory_path)):
        match = regex.match(cur)
        if match:
            version.add_file(
                VersionFile(
                    url=os.path.join(settings.base_url, main_dir, sub_dir, cur),
                    target=match.group(1),
                    type=match.group(2) + "_" + match.group(4),
                    sha256=getSHA256(os.path.join(directory_path, cur)),
                )
            )
    return version


def checkFiles(total_files: int, min_files: int, sub_dir: str) -> None:
    if total_files < min_files:
        raise Exception(
            f"Count of files ({total_files}) in {sub_dir} lower than minimum limit {min_files}"
        )


def addFilesToVersion(version: Version, main_dir: str, sub_dir: str) -> Version:
    if main_dir == "firmware":
        version = firmwareAddFilesToVersion(version, main_dir, sub_dir)
        min_files = settings.firmware_minimum_files
    elif main_dir == "qFlipper":
        version = qFlipperAddFilesToVersion(version, main_dir, sub_dir)
        min_files = settings.qFlipper_minimum_files
    checkFiles(len(version.files), min_files, sub_dir)
    return version


def parseDevChannel(channel: Channel, directory: str) -> Channel:
    version = indexer_github.getDevDetails(directory)
    version = addFilesToVersion(version, directory, "dev")
    channel.add_version(version)
    return channel


def parseRelease(channel: Channel, directory: str, isRC: bool) -> Channel:
    version = indexer_github.getReleaseDetails(directory, isRC)
    version = addFilesToVersion(version, directory, version.version)
    channel.add_version(version)
    return channel


def parseChannel(channel: Channel, directory: str) -> Channel:
    if channel == development_channel:
        channel = parseDevChannel(channel, directory)
    elif channel == release_candidate_channel:
        channel = parseRelease(channel, directory, isRC=True)
    elif channel == release_channel:
        channel = parseRelease(channel, directory, isRC=False)
    else:
        raise Exception("Unknown channel to parse")
    return channel


def parseDirectory(directory: str) -> dict:
    json = Index()
    json.add_channel(parseChannel(copy.deepcopy(development_channel), directory))
    json.add_channel(parseChannel(copy.deepcopy(release_candidate_channel), directory))
    json.add_channel(parseChannel(copy.deepcopy(release_channel), directory))
    return json.dict()
