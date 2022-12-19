from fastapi import Request
from .settings import settings


def checkToken(request: Request) -> bool:
    if request.url.path in settings.public_paths:
        return True
    return request.headers.get("Token", None) == settings.token
