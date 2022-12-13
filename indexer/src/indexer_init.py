import os
from .settings import settings
from .directory_json import generate_index


def createAppDir(app_dir):
    if not os.path.isdir(app_dir):
        os.makedirs(app_dir)


def init():
    createAppDir(settings.files_dir)
    generate_index()
