import os
import logging
from .settings import settings
from .directories import firmware_index, qFlipper_index


def createAppDir(app_dir: str) -> None:
    if not os.path.isdir(app_dir):
        os.makedirs(app_dir)


def init() -> None:
    createAppDir(settings.files_dir)
    try:
        firmware_index()
    except Exception:
        logging.error("firmware reindex failed!")

    try:
        qFlipper_index()
    except Exception:
        logging.error("qFlipper reindex failed!")
