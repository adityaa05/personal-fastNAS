from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pathlib import Path
from typing import List
import datetime
from fastapi.responses import FileResponse, StreamingResponse
import mimetypes
import os
from PIL import Image
import io
from pydantic import BaseModel
import shutil


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
                image_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
                results.append(
                    {
                        "filename": file_loc.name,
                        "path": file_loc,
                        "size": str(file_loc.relative_to(Base_Dir)),
                        "modification_at": file_loc.stat().st_mtime,
                        "folder": str(file_loc.parent.relative_to(Base_Dir)),
                        "thumbnail_url": (
                            f"/api/thumbnail/{file_loc.relative_to(Base_Dir)}"
                            if file_loc.suffix.lower() in image_ext
                            else None
                        ),
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
def preview_img_thumbnails(file_path: str, size: int = 200, format: str = "jpeg"):
    # Validate format parameter
    valid_formats = ["jpeg", "png", "webp"]
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=400, detail=f"Invalid format. Must be one of: {valid_formats}"
        )

    # Normalize format
    output_format = format.upper()  # Pillow expects uppercase
    if output_format == "JPEG":
        output_format = "JPEG"
        media_type = "image/jpeg"
    elif output_format == "PNG":
        output_format = "PNG"
        media_type = "image/png"
    elif output_format == "WEBP":
        output_format = "WEBP"
        media_type = "image/webp"

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

            # Save with format-specific options
        if output_format == "JPEG":
            img.save(buffer, format="JPEG", quality=85)
        elif output_format == "PNG":
            img.save(buffer, format="PNG", optimize=True)
        elif output_format == "WEBP":
            img.save(buffer, format="WEBP", quality=85)

        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type=f"image/{format}",
            headers={"Cache-Control": "public, max-age = 3600"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generatign thumbnail:{str(e)}"
        )


# folder creation endpoint
class FolderCreate(BaseModel):
    folder_path: str
    folder_name: str


@app.post("/api/folders/create")
def create_folder(folder_data: FolderCreate):

    parent_path = Base_Dir / folder_data.folder_path
    new_folder_path = parent_path / folder_data.folder_name

    # Security check on parent path
    try:
        parent_resolved = parent_path.resolve()
        base_resolved = Base_Dir.resolve()
        parent_resolved.relative_to(base_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if parent directory exists
    if not parent_resolved.exists():
        raise HTTPException(status_code=404, detail="Parent directory not found")

    # Check if parent is actually a directory
    if not parent_resolved.is_dir():
        raise HTTPException(status_code=400, detail="Parent path is not a directory")

    # Security check on new folder path
    try:
        new_folder_resolved = new_folder_path.resolve()
        new_folder_resolved.relative_to(base_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if folder already exists
    if new_folder_resolved.exists():
        raise HTTPException(status_code=400, detail="Folder already exists")

    # Validate folder name (no special characters that could cause issues)
    import re

    if not re.match(r"^[\w\-. ]+$", folder_data.folder_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid folder name. Use only letters, numbers, spaces, hyphens, underscores, and dots",
        )

    try:
        new_folder_resolved.mkdir(parents=False, exist_ok=False)

        return {
            "success": True,
            "message": f"Folder {folder_data.folder_name} created successfully",
            "path": str(new_folder_resolved.relative_to(base_resolved)),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")


# folder and files delete endpoint
@app.delete("/api/delete/{item_path:path}")
def delete_item(item_path: str, force: bool = False):

    # Build full path
    full_path = Base_Dir / item_path

    # Security check
    try:
        full_path_resolved = full_path.resolve()
        base_resolved = Base_Dir.resolve()
        full_path_resolved.relative_to(base_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if item exists
    if not full_path_resolved.exists():
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        # Handle file deletion
        if full_path_resolved.is_file():
            full_path_resolved.unlink()
            return {
                "success": True,
                "message": f"File '{full_path_resolved.name}' deleted successfully",
                "type": "file",
            }

        # Handle folder deletion
        elif full_path_resolved.is_dir():
            # Check if folder is empty
            if any(full_path_resolved.iterdir()):
                # Folder is not empty
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Folder is not empty. Use force=true to delete non-empty folders",
                    )
                # Force delete (remove folder and all contents
                shutil.rmtree(full_path_resolved)
                return {
                    "success": True,
                    "message": f"Folder '{full_path_resolved.name}' and all contents deleted",
                    "type": "folder",
                    "forced": True,
                }
            else:
                # Folder is empty
                full_path_resolved.rmdir()
                return {
                    "success": True,
                    "message": f"Empty folder '{full_path_resolved.name}' deleted",
                    "type": "folder",
                }

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Permission denied: Cannot delete this item"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@app.get("/api/stream/{file_path:path}")
async def stream_video(file_path: str, request: Request):
    """Stream video files with range request support"""

    # Build full path
    full_path = Base_Dir / file_path

    # Security check
    try:
        full_path_resolved = full_path.resolve()
        base_resolved = Base_Dir.resolve()
        full_path_resolved.relative_to(base_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if file exists
    if not full_path_resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Check if it's a file
    if not full_path_resolved.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Check if it's a video file
    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"]
    if full_path_resolved.suffix.lower() not in video_extensions:
        raise HTTPException(status_code=400, detail="File is not a video")

    # Get file size
    file_size = full_path_resolved.stat().st_size

    # Get range header from request (for seeking in video)
    range_header = request.headers.get("range")

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(full_path_resolved))
    if not mime_type:
        mime_type = "video/mp4"

    # Handle range request (for video seeking)
    if range_header:
        # Parse range header (format: "bytes=start-end")
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = (
            int(byte_range[1])
            if len(byte_range) > 1 and byte_range[1]
            else file_size - 1
        )

        # Calculate content length
        content_length = end - start + 1

        # Open file and seek to start position
        def iterfile():
            with open(full_path_resolved, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)  # 8KB chunks
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        # Return partial content (206 status)
        return StreamingResponse(
            iterfile(),
            status_code=206,  # Partial Content
            media_type=mime_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )

    # No range request - stream entire file
    else:

        def iterfile():
            with open(full_path_resolved, "rb") as f:
                while chunk := f.read(8192):  # 8KB chunks
                    yield chunk

        return StreamingResponse(
            iterfile(),
            media_type=mime_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )
