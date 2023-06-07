import os
import re
import shutil
import logging
import asyncio
import tempfile
from typing import List
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .directories import indexes
from .settings import settings


router = APIRouter()
lock = asyncio.Lock()
# it's global just for speed up via regex pre-compiling on app start
__reindex_regexp__ = re.compile(r"^((\d+\.\d+\.\d+)($|(-rc$)))|dev$")


def is_directory_reindex_needed(branch: str) -> bool:
    return bool(__reindex_regexp__.match(branch))


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


def save_files(path: str, files: List[UploadFile]) -> None:
    cleanup_dir(path)
    for file in files:
        filepath = os.path.join(path, file.filename)
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
    """
    A method to upload files in a certain directory
    Args:
        directory: Repository name
        files: File list
        branch: Branch name

    Returns:
        Upload status
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)

    reindex_dir = indexes.get(directory)
    path = os.path.join(settings.files_dir, directory, branch)

    try:
        check_if_path_inside_allowed_path(settings.files_dir, path)
    except Exception as e:
        logging.exception(e)
        return JSONResponse(str(e), status_code=500)

    async with lock:
        try:
            with tempfile.TemporaryDirectory() as temp_path:
                save_files(temp_path, files)
                move_files(path, temp_path)
            logging.info(f"Uploaded {len(files)} files")
        except Exception as e:
            logging.exception(e)
            return JSONResponse(e, status_code=500)
        if is_directory_reindex_needed():
            try:
                reindex_dir.reindex()
                return JSONResponse("File uploaded, reindexing is done!")
            except Exception as e:
                return JSONResponse(
                    f"File uploaded, but error occurred during re-indexing: {e}",
                    status_code=500,
                )
        else:
            return JSONResponse("File uploaded, reindexing isn't needed!")
