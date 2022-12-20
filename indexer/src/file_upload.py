import os
import shutil
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .settings import settings
import logging
import asyncio
from .directories import indexes


router = APIRouter()
lock = asyncio.Lock()


def checkIfPathInsideAllowedPath(allowed_path: str, path: str) -> None:
    allowed_path = os.path.abspath(allowed_path)
    user_path = os.path.abspath(path)
    if not user_path.startswith(allowed_path + os.sep):
        raise Exception(f"User specified path {path} is not inside {allowed_path}")


def cleanupCreateDir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    os.makedirs(path, exist_ok=True)


def saveFiles(path: str, safepath: str, files: list[UploadFile]) -> None:
    cleanupCreateDir(path)
    for file in files:
        filepath = os.path.join(path, file.filename)
        checkIfPathInsideAllowedPath(safepath, filepath)
        with open(filepath, "wb") as out_file:
            out_file.write(file.file.read())


def moveFiles(dest_dir: str, source_dir: str) -> None:
    cleanupCreateDir(dest_dir)
    for file in os.listdir(source_dir):
        sourcefilepath = os.path.join(source_dir, file)
        destfilepath = os.path.join(dest_dir, file)
        shutil.move(sourcefilepath, destfilepath)


@router.post("/{directory}/uploadfiles")
async def create_upload_files(
    directory: str, files: list[UploadFile], branch: str = Form()
):
    path = os.path.join(settings.files_dir, directory, branch)
    temp_path = os.path.join(settings.temp_dir, directory, branch)
    async with lock:
        try:
            checkIfPathInsideAllowedPath(settings.temp_dir, temp_path)
            saveFiles(temp_path, settings.temp_dir, files)
            moveFiles(path, temp_path)
            logging.info(f"Uploaded {len(files)} files")
        except Exception as e:
            logging.exception(e)
            return JSONResponse("upload fail", status_code=500)
        if directory in indexes.keys():
            try:
                indexes.get(directory).reindex
                return JSONResponse("ok")
            except Exception:
                return JSONResponse(
                    f"upload passed, but {directory} reindex fail", status_code=500
                )
        else:
            return JSONResponse("ok")
