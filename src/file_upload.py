import os
import shutil
from fastapi import APIRouter
from fastapi import Form
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from .settings import settings
from .directory_json import generate_index


router = APIRouter()


def cleanupCleateDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def saveFiles(path, files):
    for file in files:
        with open(os.path.join(path, file.filename), "wb") as out_file:
            out_file.write(file.file.read())


@router.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile], branch: str = Form()):
    path = os.path.join(settings.files_dir, branch)
    cleanupCleateDir(path)
    saveFiles(path, files)
    print(f"Uploaded {len(files)} files")
    generate_index()
    return JSONResponse("ok")
