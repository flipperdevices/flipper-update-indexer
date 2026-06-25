#!/usr/bin/env python3
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from src import directories, file_upload, security, serving
from src.repository import indexes, raw_file_upload_directories
from src.storage import storage
from src.settings import settings
from pygelf import GelfTcpHandler

app = FastAPI(docs_url=None, redoc_url=None)


@app.middleware("http")
async def check_token(request: Request, call_next):
    if security.check_token(request):
        return await call_next(request)
    return Response(status_code=401)


@app.on_event("startup")
def startup_event() -> None:
    storage.ensure_root()
    for index in indexes:
        try:
            storage.ensure_dir(index)
            indexes[index].reindex()
        except Exception:
            logging.exception(f"Init {index} reindex failed")
    for raw_upload_dir in raw_file_upload_directories:
        try:
            storage.ensure_dir(raw_upload_dir)
        except Exception:
            logging.exception(f"Failed to create {raw_upload_dir}")


# serving router is included before directories so /builds/<path>, /health and
# /ready win over the /{directory}/... catch-all routes
app.include_router(file_upload.router)
app.include_router(serving.router)
app.include_router(directories.router)


def main() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.WARN)
    if settings.kubernetes_namespace and settings.gelf_host and settings.gelf_port:
        handler = GelfTcpHandler(
            host=settings.gelf_host,
            port=settings.gelf_port,
            _kubernetes_namespace_name=settings.kubernetes_namespace,
            _kubernetes_labels_app=settings.kubernetes_app,
            _kubernetes_container_name=settings.kubernetes_container,
            _kubernetes_pod_name=settings.kubernetes_pod,
        )
        logger.addHandler(handler)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        workers=settings.workers,
        log_config=None,
    )


if __name__ == "__main__":
    main()
