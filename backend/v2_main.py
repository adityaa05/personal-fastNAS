from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Request,
    Depends,
    Header,
    BackgroundTasks,
    status,
    HTMLResponse,
)
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pathlib import Path
from typing import List, Optional, Dict, Any
import mimetypes
import os
from PIL import Image
import io
from pydantic import BaseModel, Field, field_validator
import shutil
import hashlib
import logging
import json
from contextlib import asynccontextmanager
import asyncio
from functools import lru_cache
import time
import secrets
from collections import defaultdict
from datetime import timedelta, datetime
import threading

# ============================================================================
# CONFIGURATION & SETTINGS
# ============================================================================


class Settings(BaseModel):
    """Application settings with validation"""

    BASE_DIR: Path = Path(
        os.getenv("NAS_BASE_DIR", "/Users/adityaa/Desktop/test_storage")
    )
    MAX_UPLOAD_SIZE: int = int(
        os.getenv("MAX_UPLOAD_SIZE", 100 * 1024 * 1024)
    )  # 100MB default
    ALLOWED_EXTENSIONS: List[str] = [
        ".txt",
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".mp4",
        ".mkv",
        ".zip",
        ".doc",
        ".docx",
        ".mp3",
        ".webp",
    ]
    THUMBNAIL_SIZE: int = 200
    CHUNK_SIZE: int = 8192  # 8KB for streaming
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    API_KEY: str = os.getenv("API_KEY", "your-secret-api-key-change-this")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds

    @field_validator("BASE_DIR")
    @classmethod
    def validate_base_dir(cls, v):
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v.resolve()


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()


# ============================================================================
# STRUCTURED LOGGING SETUP
# ============================================================================


def setup_logging():
    """Configure structured JSON logging for production"""
    logging.basicConfig(
        level=get_settings().LOG_LEVEL,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )


class StructuredLogger:
    """JSON structured logger for better observability"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: str, message: str, **kwargs):
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        getattr(self.logger, level.lower())(json.dumps(log_data))

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)


logger = StructuredLogger(__name__)

# ============================================================================
# RATE LIMITING
# ============================================================================


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, identifier: str, max_requests: int, window: int) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[identifier] = [
            req_time
            for req_time in self.requests[identifier]
            if now - req_time < window
        ]

        if len(self.requests[identifier]) >= max_requests:
            return False

        self.requests[identifier].append(now)
        return True


rate_limiter = RateLimiter()

# ============================================================================
# LIFESPAN & STARTUP/SHUTDOWN
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info("NAS Server starting", base_dir=str(settings.BASE_DIR))

    # Ensure base directory exists
    settings.BASE_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    logger.info("NAS Server shutting down")


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Personal NAS Server",
    description="Production-ready personal NAS for single-user storage on old laptops",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=(
        "/docs" if os.getenv("ENVIRONMENT", "development") == "development" else None
    ),  # Hide docs in production
    redoc_url=None,  # Disable redoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================================
# SECURITY & AUTHENTICATION
# ============================================================================


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Simple API key authentication"""
    settings = get_settings()
    if settings.ENABLE_AUTH:
        if not x_api_key or x_api_key != settings.API_KEY:
            logger.warning("Unauthorized access attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
    return x_api_key


async def check_rate_limit(request: Request):
    """Rate limiting middleware"""
    settings = get_settings()
    client_ip = request.client.host

    if not rate_limiter.is_allowed(
        client_ip, settings.RATE_LIMIT_REQUESTS, settings.RATE_LIMIT_WINDOW
    ):
        logger.warning("Rate limit exceeded", client_ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )


def validate_path_security(path: Path, base_dir: Path) -> Path:
    """Validate path to prevent directory traversal attacks"""
    try:
        resolved = path.resolve()
        resolved.relative_to(base_dir.resolve())
        return resolved
    except (ValueError, RuntimeError):
        logger.error("Path traversal attempt", path=str(path))
        raise HTTPException(status_code=403, detail="Access denied: Invalid path")


# ============================================================================
# REQUEST/RESPONSE MIDDLEWARE
# ============================================================================


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time * 1000, 2),
        client_ip=request.client.host,
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


class FileItem(BaseModel):
    name: str
    is_file: bool
    is_folder: bool
    file_size: int
    creation_date: datetime.datetime
    modification_date: datetime.datetime
    path: str
    extension: Optional[str] = None
    thumbnail_url: Optional[str] = None
    mime_type: Optional[str] = None


class FolderCreate(BaseModel):
    folder_path: str = Field(..., description="Parent directory path")
    folder_name: str = Field(
        ..., min_length=1, max_length=255, description="New folder name"
    )

    @field_validator("folder_name")
    @classmethod
    def validate_folder_name(cls, v):
        import re

        if not re.match(r"^[\w\-. ]+$", v):
            raise ValueError(
                "Invalid folder name. Use only alphanumeric characters, spaces, hyphens, underscores, and dots"
            )
        return v


class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    size: int
    checksum: str
    path: str
    message: str


class StorageStats(BaseModel):
    total_space: int
    used_space: int
    free_space: int
    usage_percentage: float
    total_files: int
    total_folders: int


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime.datetime
    version: str
    base_dir_accessible: bool


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# Global cache for stats
_stats_cache = {"data": None, "timestamp": None, "lock": threading.Lock()}


def get_storage_stats(base_dir: Path) -> Dict[str, Any]:
    """Get storage statistics with caching to prevent performance issues"""

    # Cache for 5 minutes
    CACHE_DURATION = timedelta(minutes=5)

    with _stats_cache["lock"]:
        now = datetime.now()

        # Return cached data if fresh
        if (
            _stats_cache["data"] is not None
            and _stats_cache["timestamp"] is not None
            and now - _stats_cache["timestamp"] < CACHE_DURATION
        ):
            return _stats_cache["data"]

        # Get disk usage (fast)
        stat = shutil.disk_usage(base_dir)

        # Count files efficiently with early exit on large directories
        file_count = 0
        folder_count = 0
        MAX_COUNT = 100000  # Safety limit

        try:
            # Use iterdir() only for immediate children, not recursive
            for item in base_dir.iterdir():
                if file_count + folder_count > MAX_COUNT:
                    break

                if item.is_file():
                    file_count += 1
                elif item.is_dir():
                    folder_count += 1
                    # Optionally count subdirectories (but slower)
                    # You can remove this for even better performance
        except PermissionError:
            pass  # Skip inaccessible directories

        result = {
            "total_space": stat.total,
            "used_space": stat.used,
            "free_space": stat.free,
            "usage_percentage": round((stat.used / stat.total) * 100, 2),
            "total_files": file_count,
            "total_folders": folder_count,
        }

        # Update cache
        _stats_cache["data"] = result
        _stats_cache["timestamp"] = now

        return result


def format_bytes(bytes_size: int) -> str:
    """Human-readable file size"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to your Personal NAS Server! 🚀",
        "version": "2.0.0",
        "docs": (
            "/docs"
            if os.getenv("ENVIRONMENT", "development") == "development"
            else "disabled"
        ),
    }


@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Health check endpoint for monitoring"""
    settings = get_settings()
    return HealthCheck(
        status="healthy",
        timestamp=datetime.datetime.utcnow(),
        version="2.0.0",
        base_dir_accessible=settings.BASE_DIR.exists() and settings.BASE_DIR.is_dir(),
    )


@app.get("/app", response_class=HTMLResponse, tags=["Frontend"])
async def serve_frontend():
    """Serve the frontend interface"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Frontend not found. Place index.html in the same directory as main.py",
        )


@app.get("/api/stats", response_model=StorageStats, tags=["Storage"])
async def get_storage_statistics(
    _: str = Depends(verify_api_key), __: None = Depends(check_rate_limit)
):
    """Get storage statistics and usage"""
    settings = get_settings()
    stats = get_storage_stats(settings.BASE_DIR)
    return StorageStats(**stats)


@app.get("/api/files", tags=["Files"])
async def list_files(
    path: str = "",
    sort_by: str = "name",  # name, size, date
    order: str = "asc",  # asc, desc
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """List files and folders with enhanced sorting"""
    settings = get_settings()

    target_dir = settings.BASE_DIR / path if path else settings.BASE_DIR
    target_dir = validate_path_security(target_dir, settings.BASE_DIR)

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    items = []
    image_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    for item in target_dir.iterdir():
        stat = item.stat()
        relative_path = str(item.relative_to(settings.BASE_DIR))
        mime_type, _ = mimetypes.guess_type(str(item))

        items.append(
            FileItem(
                name=item.name,
                is_file=item.is_file(),
                is_folder=item.is_dir(),
                file_size=stat.st_size if item.is_file() else 0,
                creation_date=datetime.datetime.fromtimestamp(
                    stat.st_birthtime
                    if hasattr(stat, "st_birthtime")
                    else stat.st_ctime
                ),
                modification_date=datetime.datetime.fromtimestamp(stat.st_mtime),
                path=relative_path,
                extension=item.suffix.lower() if item.is_file() else None,
                thumbnail_url=(
                    f"/api/thumbnail/{relative_path}"
                    if item.is_file() and item.suffix.lower() in image_ext
                    else None
                ),
                mime_type=mime_type,
            )
        )

    # Sorting
    sort_key_map = {
        "name": lambda x: x.name.lower(),
        "size": lambda x: x.file_size,
        "date": lambda x: x.modification_date,
    }

    if sort_by in sort_key_map:
        items.sort(key=sort_key_map[sort_by], reverse=(order == "desc"))

    return {"path": path, "count": len(items), "items": items}


@app.get("/api/download", tags=["Files"])
async def download_file(
    path: str, _: str = Depends(verify_api_key), __: None = Depends(check_rate_limit)
):
    """Download a file with resume support"""
    settings = get_settings()
    file_path = settings.BASE_DIR / path
    file_path = validate_path_security(file_path, settings.BASE_DIR)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    logger.info("File download", file=path, size=file_path.stat().st_size)

    return FileResponse(
        path=file_path, filename=file_path.name, media_type="application/octet-stream"
    )


@app.post("/api/upload", response_model=FileUploadResponse, tags=["Files"])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    path: str = "",
    overwrite: bool = False,
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """Upload a file with chunked processing and checksum validation"""
    settings = get_settings()

    target_dir = settings.BASE_DIR / path if path else settings.BASE_DIR
    target_dir = validate_path_security(target_dir, settings.BASE_DIR)

    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="Invalid upload directory")

    file_path = target_dir / file.filename

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    # Handle existing file
    if file_path.exists() and not overwrite:
        raise HTTPException(
            status_code=400,
            detail="File already exists. Use overwrite=true to replace.",
        )

    # Chunked upload to handle large files efficiently
    total_size = 0
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(settings.CHUNK_SIZE):
                total_size += len(chunk)

                # Check size limit
                if total_size > settings.MAX_UPLOAD_SIZE:
                    file_path.unlink(missing_ok=True)  # Clean up
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size exceeds maximum allowed size of {format_bytes(settings.MAX_UPLOAD_SIZE)}",
                    )

                f.write(chunk)
                sha256_hash.update(chunk)

        checksum = sha256_hash.hexdigest()
        relative_path = str(file_path.relative_to(settings.BASE_DIR))

        logger.info(
            "File uploaded", filename=file.filename, size=total_size, checksum=checksum
        )

        return FileUploadResponse(
            success=True,
            filename=file.filename,
            size=total_size,
            checksum=checksum,
            path=relative_path,
            message="File uploaded successfully",
        )

    except Exception as e:
        # Clean up on error
        file_path.unlink(missing_ok=True)
        logger.error("Upload failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/search", tags=["Files"])
async def search_files(
    q: str,
    file_type: Optional[str] = None,
    sort_by: str = "name",
    limit: Optional[int] = 100,
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """Search files with improved performance and filtering"""
    settings = get_settings()

    if len(q) < 2:
        raise HTTPException(
            status_code=400, detail="Search query must be at least 2 characters"
        )

    query_lower = q.lower()
    results = []
    image_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    # Use rglob for recursive search
    for file_path in settings.BASE_DIR.rglob("*"):
        if not file_path.is_file():
            continue

        # Filter by extension if specified
        if file_type and file_path.suffix.lower() != f".{file_type.lower()}":
            continue

        # Search in filename
        if query_lower in file_path.name.lower():
            stat = file_path.stat()
            relative_path = str(file_path.relative_to(settings.BASE_DIR))

            results.append(
                {
                    "filename": file_path.name,
                    "path": relative_path,
                    "size": stat.st_size,
                    "size_human": format_bytes(stat.st_size),
                    "modification_date": datetime.datetime.fromtimestamp(stat.st_mtime),
                    "folder": str(file_path.parent.relative_to(settings.BASE_DIR)),
                    "extension": file_path.suffix.lower(),
                    "thumbnail_url": (
                        f"/api/thumbnail/{relative_path}"
                        if file_path.suffix.lower() in image_ext
                        else None
                    ),
                }
            )

            if limit and len(results) >= limit:
                break

    # Sort results
    if sort_by == "size":
        results.sort(key=lambda x: x["size"], reverse=True)
    elif sort_by == "date":
        results.sort(key=lambda x: x["modification_date"], reverse=True)
    else:
        results.sort(key=lambda x: x["filename"].lower())

    return {
        "query": q,
        "file_type": file_type,
        "count": len(results),
        "results": results,
        "limited": limit is not None and len(results) >= limit,
    }


@app.get("/api/thumbnail/{file_path:path}", tags=["Files"])
async def get_thumbnail(
    file_path: str,
    size: int = 200,
    format: str = "webp",  # webp is more efficient
    _: str = Depends(verify_api_key),
):
    """Generate and cache image thumbnails"""
    settings = get_settings()

    valid_formats = ["jpeg", "png", "webp"]
    if format.lower() not in valid_formats:
        raise HTTPException(
            status_code=400, detail=f"Invalid format. Must be one of: {valid_formats}"
        )

    full_path = settings.BASE_DIR / file_path
    full_path = validate_path_security(full_path, settings.BASE_DIR)

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    image_ext = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    if full_path.suffix.lower() not in image_ext:
        raise HTTPException(status_code=400, detail="File is not an image")

    try:
        img = Image.open(full_path)
        img.thumbnail((size, size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()

        # Handle transparency
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg

        # Save with optimized settings
        output_format = format.upper()
        if output_format == "WEBP":
            img.save(buffer, format="WEBP", quality=85, method=6)
        elif output_format == "JPEG":
            img.save(buffer, format="JPEG", quality=85, optimize=True)
        else:
            img.save(buffer, format="PNG", optimize=True)

        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type=f"image/{format}",
            headers={"Cache-Control": "public, max-age=86400"},  # 24 hour cache
        )

    except Exception as e:
        logger.error("Thumbnail generation failed", file=file_path, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Error generating thumbnail: {str(e)}"
        )


@app.post("/api/folders/create", tags=["Folders"])
async def create_folder(
    folder_data: FolderCreate,
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """Create a new folder"""
    settings = get_settings()

    parent_path = settings.BASE_DIR / folder_data.folder_path
    parent_path = validate_path_security(parent_path, settings.BASE_DIR)

    if not parent_path.exists() or not parent_path.is_dir():
        raise HTTPException(status_code=404, detail="Parent directory not found")

    new_folder = parent_path / folder_data.folder_name
    new_folder = validate_path_security(new_folder, settings.BASE_DIR)

    if new_folder.exists():
        raise HTTPException(status_code=400, detail="Folder already exists")

    try:
        new_folder.mkdir(parents=False, exist_ok=False)
        logger.info(
            "Folder created", path=str(new_folder.relative_to(settings.BASE_DIR))
        )

        return {
            "success": True,
            "message": f"Folder '{folder_data.folder_name}' created successfully",
            "path": str(new_folder.relative_to(settings.BASE_DIR)),
        }
    except Exception as e:
        logger.error("Folder creation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")


@app.delete("/api/delete/{item_path:path}", tags=["Files"])
async def delete_item(
    item_path: str,
    force: bool = False,
    background_tasks: BackgroundTasks = None,
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """Delete a file or folder"""
    settings = get_settings()

    full_path = settings.BASE_DIR / item_path
    full_path = validate_path_security(full_path, settings.BASE_DIR)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        if full_path.is_file():
            full_path.unlink()
            logger.info("File deleted", path=item_path)
            return {
                "success": True,
                "message": f"File '{full_path.name}' deleted successfully",
                "type": "file",
            }

        elif full_path.is_dir():
            # Check if folder is empty
            if any(full_path.iterdir()):
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Folder is not empty. Use force=true to delete non-empty folders",
                    )
                shutil.rmtree(full_path)
                logger.info("Folder deleted (forced)", path=item_path)
                return {
                    "success": True,
                    "message": f"Folder '{full_path.name}' and all contents deleted",
                    "type": "folder",
                    "forced": True,
                }
            else:
                full_path.rmdir()
                logger.info("Empty folder deleted", path=item_path)
                return {
                    "success": True,
                    "message": f"Empty folder '{full_path.name}' deleted",
                    "type": "folder",
                }

    except PermissionError:
        logger.error("Permission denied", path=item_path)
        raise HTTPException(
            status_code=403, detail="Permission denied: Cannot delete this item"
        )
    except Exception as e:
        logger.error("Deletion failed", path=item_path, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


@app.get("/api/stream/{file_path:path}", tags=["Files"])
async def stream_video(
    file_path: str, request: Request, _: str = Depends(verify_api_key)
):
    """Stream video files with range request support (for seeking)"""
    settings = get_settings()

    full_path = settings.BASE_DIR / file_path
    full_path = validate_path_security(full_path, settings.BASE_DIR)

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v"]
    if full_path.suffix.lower() not in video_extensions:
        raise HTTPException(status_code=400, detail="File is not a video")

    file_size = full_path.stat().st_size
    range_header = request.headers.get("range")

    mime_type, _ = mimetypes.guess_type(str(full_path))
    if not mime_type:
        mime_type = "video/mp4"

    # Handle range request for seeking
    if range_header:
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = (
            int(byte_range[1])
            if len(byte_range) > 1 and byte_range[1]
            else file_size - 1
        )

        content_length = end - start + 1

        def iterfile():
            with open(full_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(settings.CHUNK_SIZE, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            iterfile(),
            status_code=206,
            media_type=mime_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Cache-Control": "public, max-age=3600",
            },
        )

    # Stream entire file
    def iterfile():
        with open(full_path, "rb") as f:
            while chunk := f.read(settings.CHUNK_SIZE):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=3600",
        },
    )


@app.get("/api/file/info/{file_path:path}", tags=["Files"])
async def get_file_info(
    file_path: str,
    include_checksum: bool = False,
    _: str = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
):
    """Get detailed file information including optional checksum"""
    settings = get_settings()

    full_path = settings.BASE_DIR / file_path
    full_path = validate_path_security(full_path, settings.BASE_DIR)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    stat = full_path.stat()
    mime_type, encoding = mimetypes.guess_type(str(full_path))

    info = {
        "name": full_path.name,
        "path": file_path,
        "size": stat.st_size,
        "size_human": format_bytes(stat.st_size),
        "extension": full_path.suffix.lower(),
        "mime_type": mime_type,
        "encoding": encoding,
        "created": datetime.datetime.fromtimestamp(
            stat.st_birthtime if hasattr(stat, "st_birthtime") else stat.st_ctime
        ),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
        "accessed": datetime.datetime.fromtimestamp(stat.st_atime),
    }

    if include_checksum:
        info["checksum_sha256"] = calculate_checksum(full_path)

    return info


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.warning(
        "HTTP exception",
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
    )


# ============================================================================
# MAIN (for local development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
        log_level="info",
    )
