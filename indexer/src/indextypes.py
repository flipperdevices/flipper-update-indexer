from pydantic import BaseModel
import re
import hashlib


class VersionFile(BaseModel):
    url: str
    target: str
    type: str
    sha256: str


class Version(BaseModel):
    version: str
    changelog: str
    timestamp: int
    files: list[VersionFile] = []

    def add_file(self, file: VersionFile) -> None:
        self.files.append(file)


class Channel(BaseModel):
    id: str
    title: str
    description: str
    versions: list[Version] = []

    def add_version(self, version: Version) -> None:
        self.versions.append(version)


class Index(BaseModel):
    channels: list[Channel] = []

    def add_channel(self, channel: Channel) -> None:
        self.channels.append(channel)


class FileParser(BaseModel):
    target: str = ""
    type: str = ""

    def getSHA256(self, filepath: str) -> str:
        with open(filepath, "rb") as file:
            file_bytes = file.read()
            sha256 = hashlib.sha256(file_bytes).hexdigest()
        return sha256

    def parse(self, filename: str) -> None:
        regex = re.compile(r"^flipper-z-(\w+)-(\w+)-([a-zA-Z0-9-_.]+)\.(\w+)$")
        match = regex.match(filename)
        if not match:
            raise Exception(f"Unknown file {filename}")
        self.target = match.group(1)
        self.type = match.group(2) + "_" + match.group(4)


development_channel = Channel(
    id="development",
    title="Development Channel",
    description="Latest builds, not yet tested by Flipper QA, be careful",
)
release_candidate_channel = Channel(
    id="release-candidate",
    title="Release Candidate Channel",
    description="This is going to be released soon, undergoing QA tests now",
)
release_channel = Channel(
    id="release",
    title="Stable Release Channel",
    description="Stable releases, tested by Flipper QA",
)
