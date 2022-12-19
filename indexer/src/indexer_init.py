import os
import logging
from .settings import settings
from .directories import indexes


def createAppDir(app_dir: str) -> None:
    if not os.path.isdir(app_dir):
        os.makedirs(app_dir)


def init() -> None:
    createAppDir(settings.files_dir)
    for index in indexes:
        indexes[index].reindex()
