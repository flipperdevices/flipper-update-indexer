class VersionFile:
    def __init__(self, url: str, target: str, file_type: str, sha256: str):
        self.url = url
        self.target = target
        self.type = file_type
        self.sha256 = sha256


class Version:
    def __init__(self, version: str, changelog: str, timestamp: int):
        self.version = version
        self.changelog = changelog
        self.timestamp = timestamp
        self.files = []

    def add_file(self, file: VersionFile):
        self.files.append(file.__dict__)


class Channel:
    def __init__(self, channel_id: str, title: str, description: str):
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
