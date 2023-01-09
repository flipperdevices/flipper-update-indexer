import os
from fastapi import Request
from .settings import settings


def checkToken(request: Request) -> bool:
    if os.path.basename(request.url.path) in settings.private_paths:
        return request.headers.get("Token", None) == settings.token
    return True
