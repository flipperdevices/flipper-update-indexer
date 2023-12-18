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
    gelf_host: str = None
    gelf_port: str = None
    kubernetes_namespace: str = None
    kubernetes_app: str = None
    kubernetes_container: str = None
    kubernetes_pod: str = None
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
    gelf_host=os.getenv("GELF_HOST"),
    gelf_port=os.getenv("GELF_PORT"),
    kubernetes_namespace=os.getenv("KUBERNETES_NAMESPACE"),
    kubernetes_app=os.getenv("KUBERNETES_APP"),
    kubernetes_container=os.getenv("KUBERNETES_CONTAINER"),
    kubernetes_pod=os.getenv("HOSTNAME"),
    firmware_github_token=os.getenv("INDEXER_FIRMWARE_GITHUB_TOKEN"),
    firmware_github_repo=os.getenv("INDEXER_FIRMWARE_GITHUB_REPO"),
    qFlipper_github_token=os.getenv("INDEXER_QFLIPPER_GITHUB_TOKEN"),
    qFlipper_github_repo=os.getenv("INDEXER_QFLIPPER_GITHUB_REPO"),
    blackmagic_github_token=os.getenv("INDEXER_BLACKMAGIC_GITHUB_TOKEN"),
    blackmagic_github_repo=os.getenv("INDEXER_BLACKMAGIC_GITHUB_REPO"),
    private_paths=["reindex", "uploadfiles", "uploadfilesraw"],
)
