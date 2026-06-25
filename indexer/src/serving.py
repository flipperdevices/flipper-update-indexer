from fastapi import APIRouter, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from .storage import storage


router = APIRouter()


@router.get("/health")
def health() -> Response:
    return JSONResponse({"status": "ok"})


@router.get("/ready")
def ready() -> Response:
    return JSONResponse({"status": "ready"})


@router.get("/builds/{path:path}")
def serve_build(path: str) -> Response:
    """
    Serve an artifact. With the local backend the file is streamed from disk;
    with the s3 backend the request is redirected to a short-lived presigned URL.
    """
    target = storage.serving_target(path)
    if target is None:
        return Response(status_code=404)
    kind, value = target
    if kind == "redirect":
        return RedirectResponse(value, status_code=302)
    return FileResponse(value)
