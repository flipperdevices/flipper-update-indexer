import os


class Settings:
    def validate(self):
        for setting in self.__dict__.keys():
            if self.__dict__[setting] == None:
                raise SystemExit(f"Setting {setting} must be set")

    def __init__(self):
        self.port = 8000
        self.workers = 1
        self.files_dir = os.getenv("INDEXER_FILES_DIR")
        self.base_url = os.getenv("INDEXER_BASE_URL")
        self.token = os.getenv("INDEXER_TOKEN")
        self.github_token = os.getenv("INDEXER_GITHUB_TOKEN")
        self.github_org = os.getenv("INDEXER_GITHUB_ORGANIZATION")
        self.github_repo = os.getenv("INDEXER_GITHUB_REPO")
        self.public_paths = ["/directory.json"]
        self.validate()


settings = Settings()
