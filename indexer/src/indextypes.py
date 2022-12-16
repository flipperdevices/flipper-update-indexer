from pydantic import BaseModel


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
    channel_id: str
    title: str
    description: str
    versions: list[Version] = []

    def add_version(self, version: Version) -> None:
        self.versions.append(version)


class Index(BaseModel):
    channels: list[Channel] = []

    def add_channel(self, channel: Channel) -> None:
        self.channels.append(channel)


development_channel = Channel(
    channel_id="development",
    title="Development Channel",
    description="Latest builds, not yet tested by Flipper QA, be careful",
)
release_candidate_channel = Channel(
    channel_id="release-candidate",
    title="Release Candidate Channel",
    description="This is going to be released soon, undergoing QA tests now",
)
release_channel = Channel(
    channel_id="release",
    title="Stable Release Channel",
    description="Stable releases, tested by Flipper QA",
)
