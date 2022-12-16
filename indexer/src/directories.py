import logging
from fastapi import APIRouter
from .dirparser import parseDirectory
from .indextypes import *
from fastapi.responses import JSONResponse

router = APIRouter()

__firmware_directory_json = Index().dict()
__qFlipper_directory_json = Index().dict()


def firmware_index() -> None:
    global __firmware_directory_json
    try:
        __firmware_directory_json = parseDirectory("firmware")
    except Exception as e:
        logging.exception(e)
        raise e


def qFlipper_index() -> None:
    global __qFlipper_directory_json
    try:
        __qFlipper_directory_json = parseDirectory("qFlipper")
    except Exception as e:
        logging.exception(e)
        raise e


@router.get("/firmware/directory.json")
def firmware_directory_request():
    return __firmware_directory_json


@router.get("/qFlipper/directory.json")
def qFlipper_directory_request():
    return __qFlipper_directory_json


@router.get("/firmware/reindex")
def firmware_reindex_request():
    try:
        firmware_index()
        return JSONResponse("ok")
    except Exception:
        return JSONResponse("fail", status_code=500)


@router.get("/qFlipper/reindex")
def qFlipper_reindex_request():
    try:
        qFlipper_index()
        return JSONResponse("ok")
    except Exception as e:
        return JSONResponse("fail", status_code=500)
