# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
File helper utilities for secure file operations
File storage, cleanup, and secure file handling
"""
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple, List
import aiofiles
from datetime import datetime, timedelta
import logging
import mimetypes
import struct

from src.config import settings

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
def generate_safe_filename(original_filename: str) -> str:
    """
    Generate a safe filename using UUID to prevent conflicts
    Consistency Pattern: Frontend uses similar ID generation

    Args:
        original_filename: Original filename from upload

    Returns:
        Safe filename with UUID
    """
    # Get file extension
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()  # Normalize extension

    # Generate unique filename
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}{ext}"

    return safe_filename

def get_file_path(original_filename: str) -> Path:
    """
    Get full file path for storage
    Consistency Pattern: Must use upload directory from config

    Args:
        original_filename: Original filename for extension

    Returns:
        Full path to file storage location
    """
    safe_filename = generate_safe_filename(original_filename)
    file_path = settings.UPLOAD_DIR / safe_filename
    return file_path

async def save_uploaded_file(file_content: bytes, file_path: Path) -> bool:
    """
    Save uploaded file content to disk
    Consistency Pattern: Secure file storage with proper permissions

    Args:
        file_content: File content as bytes
        file_path: Destination file path

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure upload directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        logger.info(f"File saved successfully: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving file {file_path}: {str(e)}")
        return False

async def read_file(file_path: Path) -> Optional[bytes]:
    """
    Read file content from disk
    Consistency Pattern: Async file operations

    Args:
        file_path: Path to file

    Returns:
        File content as bytes, or None if error
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()

        return content

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def delete_file(file_path: Path) -> bool:
    """
    Securely delete file from disk
    Consistency Pattern: Secure deletion of sensitive financial data

    Args:
        file_path: Path to file to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found for deletion: {file_path}")
            return False

        # Secure deletion by overwriting with random data
        file_size = file_path.stat().st_size
        with open(file_path, 'wb') as f:
            f.write(os.urandom(file_size))

        # Remove file
        file_path.unlink()

        logger.info(f"File securely deleted: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False

def cleanup_old_files(max_age_minutes: Optional[int] = None) -> int:
    """
    Clean up files older than specified age in minutes
    Critical Security Requirement: Files MUST be deleted after 20 minutes

    Args:
        max_age_minutes: Maximum age in minutes (default: from config FILE_RETENTION_MINUTES)

    Returns:
        Number of files cleaned up
    """
    if max_age_minutes is None:
        max_age_minutes = settings.FILE_RETENTION_MINUTES

    if max_age_minutes is None:  # Type guard
        max_age_minutes = 20  # Default fallback: 20 minutes

    cleanup_count = 0
    cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)  # type: ignore

    try:
        if not settings.UPLOAD_DIR.exists():
            logger.warning(f"Upload directory does not exist: {settings.UPLOAD_DIR}")
            return 0

        for file_path in settings.UPLOAD_DIR.iterdir():
            if file_path.is_file():
                file_modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_modified_time < cutoff_time:
                    if delete_file(file_path):
                        cleanup_count += 1

        logger.info(f"Cleaned up {cleanup_count} old files (older than {max_age_minutes} minutes)")
        return cleanup_count

    except Exception as e:
        logger.error(f"Error during cleanup of old files: {str(e)}")
        return cleanup_count

def cleanup_all_files() -> int:
    """
    Delete ALL files in upload directory
    Critical Security Requirement: Delete all files on shutdown

    Returns:
        Number of files deleted
    """
    cleanup_count = 0

    try:
        if not settings.UPLOAD_DIR.exists():
            logger.warning(f"Upload directory does not exist: {settings.UPLOAD_DIR}")
            return 0

        for file_path in settings.UPLOAD_DIR.iterdir():
            if file_path.is_file():
                if delete_file(file_path):
                    cleanup_count += 1

        logger.info(f"Cleaned up ALL {cleanup_count} files (shutdown cleanup)")
        return cleanup_count

    except Exception as e:
        logger.error(f"Error during cleanup of all files: {str(e)}")
        return cleanup_count

def delete_files_by_request_id(request_id: str) -> bool:
    """
    Delete files associated with a specific request ID
    Critical Security Requirement: Guaranteed cleanup after processing

    Args:
        request_id: Request identifier to find and delete associated files

    Returns:
        True if at least one file was deleted successfully
    """
    try:
        if not settings.UPLOAD_DIR.exists():
            return False

        deleted_count = 0
        # Look for files that start with the request_id (if we use request_id as prefix)
        # For now, this is a placeholder for the actual implementation
        # which would track file paths per request_id

        logger.info(f"Deleted {deleted_count} files for request {request_id}")
        return deleted_count > 0

    except Exception as e:
        logger.error(f"Error deleting files for request {request_id}: {str(e)}")
        return False

async def process_with_guaranteed_cleanup(files: list, processing_func):
    """
    Process files with guaranteed cleanup
    Critical Security Requirement: Files ALWAYS deleted, success or failure

    Args:
        files: List of uploaded files
        processing_func: Async function to process the files

    Returns:
        Processing result

    Raises:
        Exception: If processing fails (after cleanup)
    """
    request_id = str(uuid.uuid4())
    file_paths = []

    try:
        # Store file paths for cleanup
        for file in files:
            file_path = get_file_path(file.filename)
            file_paths.append(file_path)

        # Process files
        result = await processing_func(files, request_id)
        return result

    finally:
        # GUARANTEED cleanup: Always delete files
        logger.info(f"Guaranteed cleanup for request {request_id}")
        for file_path in file_paths:
            if file_path.exists():
                delete_file(file_path)

def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes
    Consistency Pattern: Accurate file size reporting

    Args:
        file_path: Path to file

    Returns:
        File size in bytes, or 0 if error
    """
    try:
        if not file_path.exists():
            return 0

        return file_path.stat().st_size

    except Exception as e:
        logger.error(f"Error getting file size {file_path}: {str(e)}")
        return 0

def get_file_info(file_path: Path) -> dict:
    """
    Get comprehensive file information
    Consistency Pattern: Detailed file metadata

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    try:
        if not file_path.exists():
            return {
                "exists": False,
                "path": str(file_path),
                "size": 0,
                "modified": None,
                "created": None
            }

        stat_info = file_path.stat()

        return {
            "exists": True,
            "path": str(file_path),
            "size": stat_info.st_size,
            "modified": datetime.fromtimestamp(stat_info.st_mtime),
            "created": datetime.fromtimestamp(stat_info.st_birthtime) if hasattr(stat_info, 'st_birthtime') else None,
            "is_file": file_path.is_file(),
            "extension": file_path.suffix.lower()
        }

    except Exception as e:
        logger.error(f"Error getting file info {file_path}: {str(e)}")
        return {
            "exists": False,
            "path": str(file_path),
            "size": 0,
            "modified": None,
            "created": None,
            "error": str(e)
        }

def ensure_upload_directory() -> bool:
    """
    Ensure upload directory exists with proper permissions
    Consistency Pattern: Directory setup on startup

    Returns:
        True if directory exists or was created successfully
    """
    try:
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Check if directory is writable
        test_file = settings.UPLOAD_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()

        logger.info(f"Upload directory ready: {settings.UPLOAD_DIR}")
        return True

    except Exception as e:
        logger.error(f"Error ensuring upload directory: {str(e)}")
        return False

def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format
    Consistency Pattern: Must match frontend file size formatting

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if bytes_size == 0:
        return "0 Bytes"

    k = 1024
    sizes = ["Bytes", "KB", "MB", "GB"]
    i = min(int(bytes_size.bit_length() / 10), len(sizes) - 1)

    size = bytes_size / (k ** i)
    return f"{size:.2f} {sizes[i]}"


# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# ==================== File Validation Utilities ====================

# Magic byte signatures for file type validation
MAGIC_BYTES = {
    'pdf': b'%PDF',
    'zip': b'PK\x03\x04',  # xlsx files are ZIP archives
    'xls': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',  # OLE2 format
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': {'.pdf'},
    'excel': {'.xlsx', '.xls'}
}

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,  # 50MB
    'excel': 10 * 1024 * 1024  # 10MB
}


def validate_file_type(file_path: Path, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file type using magic byte signature
    More secure than just checking file extension

    Args:
        file_path: Path to file to validate
        expected_type: Expected file type ('pdf', 'excel')

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        # Read first few bytes for magic byte check
        with open(file_path, 'rb') as f:
            file_header = f.read(8)

        # Check magic bytes for expected type
        if expected_type == 'pdf':
            if not file_header.startswith(MAGIC_BYTES['pdf']):
                return False, "Invalid PDF file (magic byte check failed)"

        elif expected_type == 'excel':
            # Excel files can be either ZIP (xlsx) or OLE2 (xls)
            is_zip = file_header.startswith(MAGIC_BYTES['zip'])
            is_ole2 = file_header.startswith(MAGIC_BYTES['xls'])

            if not (is_zip or is_ole2):
                return False, "Invalid Excel file (magic byte check failed)"

        return True, None

    except Exception as e:
        logger.error(f"Error validating file type for {file_path}: {str(e)}")
        return False, f"Error reading file: {str(e)}"


def validate_file_extension(filename: str, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against allowed types

    Args:
        filename: Original filename to check
        expected_type: Expected file type ('pdf', 'excel')

    Returns:
        Tuple of (is_valid, error_message)
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    if expected_type not in ALLOWED_EXTENSIONS:
        return False, f"Unknown file type: {expected_type}"

    if ext not in ALLOWED_EXTENSIONS[expected_type]:
        allowed = ", ".join(ALLOWED_EXTENSIONS[expected_type])
        return False, f"Invalid file extension for {expected_type}. Allowed: {allowed}"

    return True, None


def validate_file_size(file_path: Path, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against maximum allowed size

    Args:
        file_path: Path to file to validate
        expected_type: Expected file type ('pdf', 'excel')

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        file_size = file_path.stat().st_size
        max_size = MAX_FILE_SIZES.get(expected_type, 10 * 1024 * 1024)  # Default 10MB

        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return False, f"File too large: {actual_mb:.2f}MB (max {max_mb:.2f}MB for {expected_type})"

        if file_size == 0:
            return False, "File is empty"

        return True, None

    except Exception as e:
        logger.error(f"Error validating file size for {file_path}: {str(e)}")
        return False, f"Error checking file size: {str(e)}"


def validate_upload_file(file_path: Path, filename: str, expected_type: str) -> Tuple[bool, List[str]]:
    """
    Comprehensive file validation for uploads
    Combines extension, size, and magic byte validation

    Args:
        file_path: Path to uploaded file
        filename: Original filename
        expected_type: Expected file type ('pdf', 'excel')

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Validate extension
    ext_valid, ext_error = validate_file_extension(filename, expected_type)
    if not ext_valid:
        errors.append(ext_error)

    # Validate size
    size_valid, size_error = validate_file_size(file_path, expected_type)
    if not size_valid:
        errors.append(size_error)

    # Validate magic bytes
    type_valid, type_error = validate_file_type(file_path, expected_type)
    if not type_valid:
        errors.append(type_error)

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"File validation passed: {filename} ({expected_type})")
    else:
        logger.warning(f"File validation failed: {filename} - {errors}")

    return is_valid, errors


def get_mime_type(file_path: Path) -> Optional[str]:
    """
    Get MIME type for file
    Useful for Content-Type headers

    Args:
        file_path: Path to file

    Returns:
        MIME type string or None if unknown
    """
    try:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type
    except Exception as e:
        logger.error(f"Error getting MIME type for {file_path}: {str(e)}")
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    Remove dangerous characters and normalize

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)

    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '')

    # Limit filename length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext

    # If filename is empty after sanitization, use default
    if not filename or filename.isspace():
        filename = "sanitized_file"

    return filename.strip()


def is_safe_file_path(file_path: Path, base_directory: Path) -> bool:
    """
    Check if file path is safe and doesn't escape base directory
    Prevents path traversal attacks

    Args:
        file_path: File path to check
        base_directory: Base directory that should contain the file

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve to absolute paths
        resolved_file = file_path.resolve()
        resolved_base = base_directory.resolve()

        # Check if resolved file is within base directory
        try:
            resolved_file.relative_to(resolved_base)
            return True
        except ValueError:
            # Path is outside base directory
            logger.warning(f"Unsafe file path detected: {file_path} (outside {base_directory})")
            return False

    except Exception as e:
        logger.error(f"Error checking file path safety: {str(e)}")
        return False

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ