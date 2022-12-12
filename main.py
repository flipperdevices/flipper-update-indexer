#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from src import directory_json
from src import file_upload
from src import security
from src.init import init
from src.settings import settings

app = FastAPI()
app.include_router(directory_json.router)


@app.middleware("http")
async def checkToken(request: Request, call_next):
    if security.checkToken(request):
        return await call_next(request)
    return Response(status_code=401)


app.include_router(file_upload.router)


def main():
    init()
    uvicorn.run(
        "main:app", host="0.0.0.0", port=settings.port, workers=settings.workers
    )


if __name__ == "__main__":
    main()
