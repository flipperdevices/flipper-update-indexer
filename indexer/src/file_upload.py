import os
import shutil
import logging
import asyncio
from typing import List
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .directories import indexes
from .settings import settings


router = APIRouter()
lock = asyncio.Lock()


def check_if_path_inside_allowed_path(allowed_path: str, path: str) -> None:
    allowed_path = os.path.abspath(allowed_path)
    user_path = os.path.abspath(path)
    if not user_path.startswith(allowed_path + os.sep):
        raise Exception(f"User specified path {path} is not inside {allowed_path}")


def cleanup_dir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    os.makedirs(path, exist_ok=True)


def save_files(path: str, safepath: str, files: List[UploadFile]) -> None:
    cleanup_dir(path)
    for file in files:
        filepath = os.path.join(path, file.filename)
        check_if_path_inside_allowed_path(safepath, filepath)
        with open(filepath, "wb") as out_file:
            out_file.write(file.file.read())


def move_files(dest_dir: str, source_dir: str) -> None:
    cleanup_dir(dest_dir)
    for file in os.listdir(source_dir):
        sourcefilepath = os.path.join(source_dir, file)
        destfilepath = os.path.join(dest_dir, file)
        shutil.move(sourcefilepath, destfilepath)


@router.post("/{directory}/uploadfiles")
async def create_upload_files(
    directory: str, files: List[UploadFile], branch: str = Form()
):
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)

    reindex_dir = indexes.get(directory)
    path = os.path.join(settings.files_dir, directory, branch)
    temp_path = os.path.join(settings.temp_dir, directory, branch)
    async with lock:
        try:
            check_if_path_inside_allowed_path(settings.temp_dir, temp_path)
            save_files(temp_path, settings.temp_dir, files)
            move_files(path, temp_path)
            logging.info(f"Uploaded {len(files)} files")
        except Exception as e:
            logging.exception(e)
            return JSONResponse(e, status_code=500)
        try:
            reindex_dir.reindex()
            return JSONResponse("File uploaded, reindexing is done!")
        except Exception as e:
            return JSONResponse(
                f"File uploaded, but error occurred during re-indexing: {e}", status_code=500
            )
