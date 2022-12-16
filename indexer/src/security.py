from fastapi import Request
from .settings import settings


def checkToken(request: Request) -> bool:
    if request.url.path in settings.public_paths:
        return True
    if "Token" not in request.headers:
        return False
    if request.headers["Token"] != settings.token:
        return False
    return True
