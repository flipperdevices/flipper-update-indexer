import os
import shutil
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import JSONResponse
from .settings import settings
import logging
from .directories import firmware_index, qFlipper_index


router = APIRouter()


def checkIfPathInsideAllowedPath(path: str) -> None:
    allowed_path = settings.files_dir
    if not path.startswith(os.path.abspath(allowed_path) + os.sep):
        raise Exception(f"User specified path {path} is not inside {allowed_path}")


def cleanupCleateDir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    os.makedirs(path, exist_ok=True)


def saveFiles(path: str, files: list[UploadFile]) -> None:
    for file in files:
        with open(os.path.join(path, file.filename), "wb") as out_file:
            out_file.write(file.file.read())


@router.post("/{directory}/uploadfiles")
async def create_upload_files(files: list[UploadFile], branch: str = Form()):
    path = os.path.join(settings.files_dir, branch)
    try:
        checkIfPathInsideAllowedPath(path)
        cleanupCleateDir(path)
        saveFiles(path, files)
        logging.info(f"Uploaded {len(files)} files")
    except Exception as e:
        logging.exception(e)
        return JSONResponse("upload fail", status_code=500)
    if directory == "firmware":
        try:
            firmware_index()
            return JSONResponse("ok")
        except Exception:
            return JSONResponse(
                "upload passed, but firmware reindex fail", status_code=500
            )
    elif directory == "qFlipper":
        try:
            qFlipper_index()
            return JSONResponse("ok")
        except Exception:
            return JSONResponse(
                "upload passed, but qFlipper reindex fail", status_code=500
            )
    else:
        return JSONResponse("Wrong directory", status_code=404)
    return JSONResponse("ok")
