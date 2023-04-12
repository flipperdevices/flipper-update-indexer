import logging
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse

from .repository import indexes


router = APIRouter()
lock = asyncio.Lock()


@router.get("/{directory}/directory.json")
async def directory_request(directory):
    """
    Method for obtaining indices
    Args:
        directory: Repository name

    Returns:
        Indices in json
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    return indexes.get(directory).index


@router.get(
    "/{directory}/{channel}/{target}/{type}",
    response_class=RedirectResponse,
    status_code=302,
)
async def latest_request(directory, channel, target, file_type):
    """
    A method for retrieving a file from the repository
    of a specific version
    Args:
        directory: Repository name
        channel: Channel type (release, rc, dev)
        target: Operation System (linux, mac, win)
        file_type: File Type

    Returns:
        Artifact file
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    index = indexes.get(directory)
    if len(index.index["channels"]) == 0:
        return JSONResponse("No channels found!", status_code=404)
    try:
        return index.get_file_from_latest_version(channel, target, file_type)
    except Exception as e:
        return JSONResponse(e, status_code=404)


@router.post("/{directory}/reindex")
async def reindex_request(directory):
    """
    Method for starting reindexing
    Args:
        directory: Repository name

    Returns:
        Reindex status
    """
    if directory not in indexes:
        return JSONResponse(f"{directory} not found!", status_code=404)
    async with lock:
        try:
            indexes.get(directory).reindex()
            return JSONResponse("Reindexing is done!")
        except Exception as e:
            logging.exception(e)
            return JSONResponse("Reindexing is failed!", status_code=500)
