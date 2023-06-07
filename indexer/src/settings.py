import os
from pydantic import BaseModel
from typing import List


class Settings(BaseModel):
    port: int
    workers: int
    files_dir: str
    base_url: str
    token: str
    github_org: str
    firmware_github_token: str
    firmware_github_repo: str
    qFlipper_github_token: str
    qFlipper_github_repo: str
    blackmagic_github_token: str
    blackmagic_github_repo: str
    private_paths: List[str]


settings = Settings(
    port=8000,
    workers=1,
    files_dir=os.getenv("INDEXER_FILES_DIR"),
    base_url=os.getenv("INDEXER_BASE_URL"),
    token=os.getenv("INDEXER_TOKEN"),
    github_org=os.getenv("INDEXER_GITHUB_ORGANIZATION"),
    firmware_github_token=os.getenv("INDEXER_FIRMWARE_GITHUB_TOKEN"),
    firmware_github_repo=os.getenv("INDEXER_FIRMWARE_GITHUB_REPO"),
    qFlipper_github_token=os.getenv("INDEXER_QFLIPPER_GITHUB_TOKEN"),
    qFlipper_github_repo=os.getenv("INDEXER_QFLIPPER_GITHUB_REPO"),
    blackmagic_github_token=os.getenv("INDEXER_BLACKMAGIC_GITHUB_TOKEN"),
    blackmagic_github_repo=os.getenv("INDEXER_BLACKMAGIC_GITHUB_REPO"),
    private_paths=["reindex", "uploadfiles"],
)
