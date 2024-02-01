import os
import re
import shutil
import logging
import asyncio
import tempfile
from typing import List
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .repository import indexes, raw_file_upload_directories
from .settings import settings


router = APIRouter()
lock = asyncio.Lock()
# it's global just for speed up via regex pre-compiling on app start
__reindex_regexp__ = re.compile(r"^((\d+\.\d+\.\d+)($|(-rc$)))|dev$")

TOKEN_FILENAME = ".version_id"


def is_directory_reindex_needed(branch: str) -> bool:
    return bool(__reindex_regexp__.match(branch))


def check_if_path_inside_allowed_path(allowed_path: str, path: str) -> None:
    allowed_path = os.path.abspath(allowed_path)
    user_path = os.path.abspath(path)
    if not user_path.startswith(allowed_path + os.sep):
        exception_msg = f"User specified path {path} is not inside {allowed_path}"
        logging.exception(exception_msg)
        raise Exception(exception_msg)


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


def move_files_for_indexed(dest_dir: str, source_dir: str, version_token: str) -> None:
    token_file_path = os.path.join(dest_dir, TOKEN_FILENAME)
    do_cleanup = False
    if version_token and os.path.isfile(token_file_path):
        with open(token_file_path, "r") as token_file:
            if token_file.read() != version_token:
                do_cleanup = True
    else:
        do_cleanup = True
    if do_cleanup:
        cleanup_dir(dest_dir)
        if version_token:
            with open(token_file_path, "w") as token_file:
                token_file.write(version_token)

    for file in os.listdir(source_dir):
        sourcefilepath = os.path.join(source_dir, file)
        destfilepath = os.path.join(dest_dir, file)
        shutil.move(sourcefilepath, destfilepath)


def move_files_raw(dest_dir: str, source_dir: str) -> None:
    for file in os.listdir(source_dir):
        sourcefilepath = os.path.join(source_dir, file)
        destfilepath = os.path.join(dest_dir, file)
        shutil.move(sourcefilepath, destfilepath)


@router.post("/{directory}/uploadfiles")
async def create_upload_files(
    directory: str,
    files: List[UploadFile],
    branch: str = Form(),
    version_token: str = Form(default=""),
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
    project_root_path = os.path.join(settings.files_dir, directory)
    final_path = os.path.join(project_root_path, branch)

    try:
        check_if_path_inside_allowed_path(project_root_path, final_path)
    except Exception as e:
        logging.exception(e)
        return JSONResponse(str(e), status_code=500)

    async with lock:
        try:
            with tempfile.TemporaryDirectory() as temp_path:
                save_files(temp_path, files)
                move_files_for_indexed(final_path, temp_path, version_token)
            logging.info(f"Uploaded {len(files)} files")
        except Exception as e:
            logging.exception(e)
            return JSONResponse(str(e), status_code=500)
        if is_directory_reindex_needed(branch):
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


@router.post("/{directory}/uploadfilesraw")
async def create_upload_files_raw(
    directory: str,
    files: List[UploadFile],
):
    """
    A method to upload files in a certain directory without indexing
    Args:
        directory: Repository name
        files: File list

    Returns:
        Upload status
    """
    if directory not in raw_file_upload_directories:
        return JSONResponse(f"{directory} not found!", status_code=404)

    project_root_path = os.path.join(settings.files_dir, directory)

    async with lock:
        try:
            with tempfile.TemporaryDirectory() as temp_path:
                save_files(temp_path, files)
                move_files_raw(project_root_path, temp_path)
            logging.info(f"Uploaded {len(files)} files")
            return JSONResponse("File uploaded")
        except Exception as e:
            logging.exception(e)
            return JSONResponse(str(e), status_code=500)
