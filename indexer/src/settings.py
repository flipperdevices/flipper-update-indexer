import os
from pydantic import BaseModel
from typing import List, Optional


def _split_env(name: str) -> List[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


# Every directory the upstream indexer knows how to build. A Busy-only instance
# enables just "busybar-firmware" via INDEXER_ENABLED_DIRECTORIES.
ALL_DIRECTORIES = [
    "firmware",
    "qFlipper",
    "blackmagic-firmware",
    "vgm-firmware",
    "busybar-firmware",
    "flipper-one-mcu",
]


class Settings(BaseModel):
    port: int
    workers: int
    files_dir: Optional[str] = None  # required only for the local storage backend
    base_url: str
    token: str
    github_org: Optional[str] = None
    enabled_directories: List[str]
    raw_upload_directories: List[str]
    # storage backend: "local" (filesystem, default) or "s3" (S3-compatible)
    storage_backend: str
    s3_bucket: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    s3_region: Optional[str] = None
    s3_prefix: str = ""
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    # optional GELF logging
    gelf_host: Optional[str] = None
    gelf_port: Optional[str] = None
    kubernetes_namespace: Optional[str] = None
    kubernetes_app: Optional[str] = None
    kubernetes_container: Optional[str] = None
    kubernetes_pod: Optional[str] = None
    # per-directory GitHub config; only enabled directories need their values
    firmware_github_token: Optional[str] = None
    firmware_github_repo: Optional[str] = None
    qFlipper_github_token: Optional[str] = None
    qFlipper_github_repo: Optional[str] = None
    blackmagic_github_token: Optional[str] = None
    blackmagic_github_repo: Optional[str] = None
    vgm_github_token: Optional[str] = None
    vgm_github_repo: Optional[str] = None
    busybar_github_token: Optional[str] = None
    busybar_github_repo: Optional[str] = None
    flipper_one_mcu_github_token: Optional[str] = None
    flipper_one_mcu_github_repo: Optional[str] = None
    private_paths: List[str]


_enabled_directories = _split_env("INDEXER_ENABLED_DIRECTORIES") or list(
    ALL_DIRECTORIES
)
_raw_upload_directories = (
    _split_env("INDEXER_RAW_UPLOAD_DIRECTORIES")
    if os.getenv("INDEXER_RAW_UPLOAD_DIRECTORIES") is not None
    else ["toolchain"]
)


settings = Settings(
    port=8000,
    workers=1,
    files_dir=os.getenv("INDEXER_FILES_DIR"),
    base_url=os.getenv("INDEXER_BASE_URL"),
    token=os.getenv("INDEXER_TOKEN"),
    github_org=os.getenv("INDEXER_GITHUB_ORGANIZATION"),
    enabled_directories=_enabled_directories,
    raw_upload_directories=_raw_upload_directories,
    storage_backend=os.getenv("INDEXER_STORAGE_BACKEND", "local"),
    s3_bucket=os.getenv("INDEXER_S3_BUCKET"),
    s3_endpoint_url=os.getenv("INDEXER_S3_ENDPOINT_URL"),
    s3_region=os.getenv("INDEXER_S3_REGION"),
    s3_prefix=os.getenv("INDEXER_S3_PREFIX", ""),
    s3_access_key_id=os.getenv("INDEXER_S3_ACCESS_KEY_ID"),
    s3_secret_access_key=os.getenv("INDEXER_S3_SECRET_ACCESS_KEY"),
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
    vgm_github_token=os.getenv("INDEXER_VGM_GITHUB_TOKEN"),
    vgm_github_repo=os.getenv("INDEXER_VGM_GITHUB_REPO"),
    busybar_github_token=os.getenv("INDEXER_BUSYBAR_GITHUB_TOKEN"),
    busybar_github_repo=os.getenv("INDEXER_BUSYBAR_GITHUB_REPO"),
    flipper_one_mcu_github_token=os.getenv("INDEXER_FLIPPER_ONE_MCU_GITHUB_TOKEN"),
    flipper_one_mcu_github_repo=os.getenv("INDEXER_FLIPPER_ONE_MCU_GITHUB_REPO"),
    private_paths=[
        "reindex",
        "uploadfiles",
        "uploadfilesraw",
        *_split_env("INDEXER_PRIVATE_PATHS"),
    ],
)
