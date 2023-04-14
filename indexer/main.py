#!/usr/bin/env python3
import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from src import directories, file_upload, security
from src.directories import indexes
from src.settings import settings

app = FastAPI(docs_url=None, redoc_url=None)


@app.middleware("http")
async def check_token(request: Request, call_next):
    if security.check_token(request):
        return await call_next(request)
    return Response(status_code=401)


@app.on_event("startup")
def startup_event() -> None:
    if not os.path.isdir(settings.files_dir):
        os.makedirs(settings.files_dir)
    for index in indexes:
        try:
            indexes[index].reindex()
        except Exception:
            logging.exception(f"Init {index} reindex failed")


app.include_router(file_upload.router)
app.include_router(directories.router)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(levelname)s[%(filename)s:%(funcName)s]: %(message)s",
    )
    uvicorn.run(
        "main:app", host="0.0.0.0", port=settings.port, workers=settings.workers
    )


if __name__ == "__main__":
    main()
