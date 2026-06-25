import re
import logging
import asyncio
from typing import List
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .repository import indexes, raw_file_upload_directories
from .storage import storage


router = APIRouter()
lock = asyncio.Lock()
# it's global just for speed up via regex pre-compiling on app start
__reindex_regexp__ = re.compile(r"^((\d+\.\d+\.\d+)($|(-rc$)))|dev$")

TOKEN_FILENAME = ".version_id"


def is_directory_reindex_needed(branch: str) -> bool:
    return bool(__reindex_regexp__.match(branch))


def is_branch_safe(branch: str) -> bool:
    # branch may contain slashes (e.g. "user/feature") but must not escape the directory
    return all(part not in ("", ".", "..") for part in branch.split("/"))


def store_indexed_files(
    directory: str, branch: str, files: List[UploadFile], version_token: str
) -> None:
    stored_token = None
    if version_token and storage.file_exists(directory, branch, TOKEN_FILENAME):
        stored_token = storage.read(directory, branch, TOKEN_FILENAME).decode()
    # wipe the branch when it holds a different build (or no version token is given),
    # otherwise keep existing files and just add/overwrite the uploaded ones
    if not version_token or stored_token != version_token:
        storage.delete_tree(directory, branch)
        if version_token:
            storage.write(version_token.encode(), directory, branch, TOKEN_FILENAME)
    for file in files:
        storage.write(file.file.read(), directory, branch, file.filename)


def store_raw_files(directory: str, files: List[UploadFile]) -> None:
    for file in files:
        storage.write(file.file.read(), directory, file.filename)


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
    if not is_branch_safe(branch):
        return JSONResponse(f"Invalid branch name: {branch}", status_code=400)

    reindex_dir = indexes.get(directory)

    async with lock:
        try:
            store_indexed_files(directory, branch, files, version_token)
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

    async with lock:
        try:
            store_raw_files(directory, files)
            logging.info(f"Uploaded {len(files)} files")
            return JSONResponse("File uploaded")
        except Exception as e:
            logging.exception(e)
            return JSONResponse(str(e), status_code=500)
