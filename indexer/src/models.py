import re
import hashlib
from pydantic import BaseModel
from typing import List


class VersionFile(BaseModel):
    url: str
    target: str
    type: str
    sha256: str


class Version(BaseModel):
    version: str
    changelog: str
    timestamp: int
    files: List[VersionFile] = []

    def add_file(self, file: VersionFile) -> None:
        self.files.append(file)


class Channel(BaseModel):
    id: str
    title: str
    description: str
    versions: List[Version] = []

    def add_version(self, version: Version) -> None:
        self.versions.append(version)


class Index(BaseModel):
    channels: List[Channel] = []

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
        regex = re.compile(
            r"^flipper-z-(\w+)-(\w+)-([0-9.]+(-rc)?|(dev-\w+-\w+))\.(\w+)$"
        )
        match = regex.match(filename)
        if not match:
            raise Exception(f"Unknown file {filename}")
        self.target = match.group(1)
        self.type = match.group(2) + "_" + match.group(6)


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
                raise Exception(f"Cannot parse target")
        self.target = target + "/" + jsonArch
        self.type = file_type


class blackmagickFileParser(FileParser):
    def parse(self, filename: str) -> None:
        regex = re.compile(
            r"^blackmagic-firmware-(\w+)-(\w+)-([0-9.]+(-rc)?|(dev-\w+-\w+))\.(\w+)$"
        )
        match = regex.match(filename)
        if not match:
            raise Exception(f"Unknown file {filename}")
        self.target = match.group(1)
        self.type = match.group(2) + "_" + match.group(6)
