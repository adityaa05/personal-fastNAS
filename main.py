from fastapi import FastAPI, HTTPException, UploadFile, File
from pathlib import Path
from typing import List
import datetime
from fastapi.responses import FileResponse, StreamingResponse
import mimetypes
import os
from PIL import Image
import io

Base_Dir = Path("/Users/adityaa/Desktop/test_storage")
app = FastAPI(title="Aditya's NAS")


# default endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome Aditya! ;)"}


# listing files endpoint
@app.get("/api/files")
def list_files(path: str = ""):

    if path != "":
        Target_Dir = Base_Dir / path
    else:
        Target_Dir = Base_Dir

    try:
        Target_Dir_resolved = Target_Dir.resolve()
        Base_Dir_resolved = Base_Dir.resolve()

        Target_Dir_resolved.relative_to(Base_Dir_resolved)

        # if not str(Target_Dir).startswith(str(Base_Dir.resolve())):
        #     raise HTTPException(status_code= 403, detail= "Access Denied")

    except ValueError:
        raise HTTPException(status_code=403, detail="Access Denied")

    if not Target_Dir.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not Target_Dir.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    items = []
    for item in sorted(Target_Dir.iterdir()):
        creation_time = item.stat().st_birthtime
        items.append(
            {
                "name": item.name,  # here item.xyz only returns filename not the file path
                "is_file": item.is_file(),
                "is_folder": item.is_dir(),
                "file_size": item.stat().st_size,
                "creation_date": datetime.datetime.fromtimestamp(creation_time),
                "test_item": str(item),
                "test_item2": item.absolute(),
            }
        )

    return {"path": str(Base_Dir), "count": len(items), "items": items}


# listing count of files and folders too
@app.get("/api/onlyfiles")
def get_files():
    file_count = 0
    folder_count = 0

    for item in Base_Dir.iterdir():
        if item.is_file():
            file_count += 1
        else:
            folder_count += 1

    return {"total_files": file_count, "total_folders": folder_count}


# downloading a file
@app.get("/api/download/{filename}")
def download_files(filename: str):
    file_path = Base_Dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if file_path.is_dir():
        raise HTTPException(status_code=400, detail="Sorry but no folders allowed")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


# downloading a file via query - path
@app.get("/api/download")
def download_files_with_path(path: str):
    file_path = Base_Dir / path

    try:

        file_path_resolved = file_path.resolve()
        base_dir_resolved = Base_Dir.resolve()
        file_path_resolved.relative_to(base_dir_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not file_path_resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if file_path_resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a file")

    return FileResponse(
        path=file_path_resolved,
        filename=file_path_resolved.name,
        media_type="application/octet-stream",
    )


# upload a file
@app.post("/api/upload")
async def upload_files(
    file: UploadFile = File(None, description="Upload a file")
):  # will return error if no file is uploaded
    file_path = Base_Dir / file.filename
    """
    def file_rename():
        filename,  extension = os.path.splitext(file_path)
        counter = 1
        
        while True:
            new_filename = f"{filename}{counter}{extension}"
            if not os.path.exists(new_filename):
                break
            counter += 1
        os.rename(file_path, new_filename)
        return new_filename
    """

    if file_path.exists():  # check if the file already exists or not
        raise HTTPException(status_code=400, detail=" File already exists")

    contents = await file.read()  # analyse the file content
    # after reading if you want you can limit the file size too
    max_size = 2 * 1024 * 1024  # 2mb max
    allowed_filetype = [".txt", ".pdf", ".jpg", ".png", ".mp4"]
    my_filetype = Path(file.filename).suffix.lower()

    if not my_filetype in allowed_filetype:
        raise HTTPException(
            status_code=400, detail=f"File type: {my_filetype} not allowed"
        )

    if len(contents) > max_size:
        raise HTTPException(status_code=413, detail="File size is exceeding 10 MB")

    with open(file_path, "wb") as fp:
        fp.write(contents)  # push the content

    return {
        "success": True,
        "filename": file.filename,
        "size": len(contents),
        "message": "Successfully uploaded your file!",
    }


# file info endpoint (challenge)
@app.get("/api/teststat/{filename}")
def fileinfo(filename: str):
    filename = Base_Dir / filename

    if not filename.exists():
        raise HTTPException(status_code=404, detail="Not found")

    file_info = []

    file_info.append(
        {
            "name": filename.name,
            "size": filename.stat(follow_symlinks=True).st_size,
            "filetype": mimetypes.guess_type(filename),
        }
    )

    return {"data": file_info}


# searching files with fitering- search by extension
@app.get("/api/search")
def search_files(
    q: str, file_type: str = None, sort_bysize: str = "size", limit: int = None
):
    # handling insuff chars in search query
    if len(q) < 1:
        raise HTTPException(
            status_code=400, detail="Your query contains insufficient characters"
        )

    lowercase_q = q.lower()
    results = []
    for file_loc in Base_Dir.rglob("*"):
        if file_type and not file_loc.suffix.lower() == f"{file_type.lower()}":
            continue

        if lowercase_q in file_loc.name.lower():
            if file_loc.is_file:
                results.append(
                    {
                        "filename": file_loc.name,
                        "path": file_loc,
                        "size": str(file_loc.relative_to(Base_Dir)),
                        "modification_at": file_loc.stat().st_mtime,
                        "folder": str(file_loc.parent.relative_to(Base_Dir)),
                    }
                )

        if sort_bysize == "size":
            results = sorted(results, key=lambda x: x["size"].lower())

        if limit is not None and limit > 0:
            results = results[:limit]

    return {
        "query": q,
        "filetype": file_type,
        "search_count": len(results),
        "search_results": results,
        "sort_by": sort_bysize,
        "limit": limit,
    }


# thumbnail function for easy preview image
@app.get("/api/thumbnail/{file_path:path}")
def preview_img_thumbnails(file_path: str, size: int = 200):
    file_path = Base_Dir / file_path

    try:
        file_path_resolved = file_path.resolve()
        base_dir_resolved = Base_Dir.resolve()
        file_path_resolved.relative_to(base_dir_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access Denied")

    if not file_path_resolved.exists():
        raise HTTPException(status_code=404, detail=" File not found")

    if not file_path_resolved.is_file():
        raise HTTPException(status_code=400, detail=" Path is not a file")

    image_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    if file_path_resolved.suffix.lower() not in image_ext:
        raise HTTPException(status_code=400, detail=" Fole os not an image")

    try:
        img = Image.open(file_path_resolved)
        img.thumbnail((size, size))

        buffer = io.BytesIO()

        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)

            img = bg

            img.save(buffer, format="JPEG")
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age = 1800"},
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generatign thumbnail:{str(e)}"
        )
