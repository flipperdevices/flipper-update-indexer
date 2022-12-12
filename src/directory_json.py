from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json


class VersionFile:
    def __init__(self, url, target, file_type, sha256):
        self.url = url
        self.target = target
        self.file_type = file_type
        self.sha256 = sha256


class Version:
    def __init__(self, version, changelog, timestamp):
        self.version = version
        self.changelog = changelog
        self.timestamp = timestamp
        self.files = []

    def add_file(self, file: VersionFile):
        self.files.append(file.__dict__)


class Channel:
    def __init__(self, channel_id, title, description):
        self.id = channel_id
        self.title = title
        self.description = description
        self.versions = []

    def add_version(self, version: Version):
        self.versions.append(version.__dict__)


class Index:
    def __init__(self):
        self.channels = []

    def add_channel(self, channel: Channel):
        self.channels.append(channel.__dict__)


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

router = APIRouter()
directory_json = Index()
channels = [development_channel, release_candidate_channel, release_channel]


def generate_index():
    global directory_json
    directory_json = Index()
    for cur in channels:
        version = Version("0.73.1-rc", "Nothing", 123124123412)
        version.add_file(
            VersionFile(
                "ya.ru",
                "any",
                "core2_firmware_tgz",
                "3c51876f3304885e20fe364a434d222f117fc30bbf4feeaf56ca0a4ba160d60b",
            )
        )
        cur.add_version(version)
        directory_json.add_channel(cur)
    print("Reindex completed")


@router.get("/directory.json")
async def directory():
    return JSONResponse(directory_json.__dict__)


@router.get("/reindex")
async def reindex():
    generate_index()
    return JSONResponse("ok")
