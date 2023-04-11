#!/usr/bin/env python3
import sys
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from src import directories, file_upload, security, indexer_init
from src.settings import settings

app = FastAPI(docs_url=None, redoc_url=None)


@app.middleware("http")
async def check_token(request: Request, call_next):
    if security.check_token(request):
        return await call_next(request)
    return Response(status_code=401)


app.include_router(file_upload.router)
app.include_router(directories.router)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(levelname)s[%(filename)s:%(funcName)s]: %(message)s",
    )
    # indexer_init.init()
    uvicorn.run(
        "main:app", host="0.0.0.0", port=settings.port, workers=settings.workers
    )


if __name__ == "__main__":
    main()
