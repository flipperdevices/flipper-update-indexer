#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI, Request, Response
from src import directory_json, file_upload, security, indexer_init
from src.settings import settings
import sys
import logging

app = FastAPI()


@app.middleware("http")
async def checkToken(request: Request, call_next):
    if security.checkToken(request):
        return await call_next(request)
    return Response(status_code=401)


app.include_router(file_upload.router)
app.include_router(directory_json.router)


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    indexer_init.init()
    uvicorn.run(
        "main:app", host="0.0.0.0", port=settings.port, workers=settings.workers
    )


if __name__ == "__main__":
    main()
