import os
from .settings import settings


def init():
    if not os.path.isdir(settings.files_dir):
        os.makedirs(settings.files_dir)
