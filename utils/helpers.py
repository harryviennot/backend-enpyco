"""
Utility helper functions for the Memoir Generator.
"""
import os
import re
import uuid
from typing import Optional, Tuple
from datetime import datetime


# File validation constants
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
# Note: Supabase free tier has a 50MB file size limit
# To upload larger files, upgrade to Supabase Pro ($25/mo) which supports up to 5GB per file
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file_type(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if the file type is supported.

    Args:
        filename: Name of the file

    Returns:
        Tuple of (is_valid, error_message)
    """
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        return False, "File has no extension"

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Only {', '.join(ALLOWED_EXTENSIONS)} are allowed."

    return True, None


def validate_file_size(file_size: int) -> Tuple[bool, Optional[str]]:
    """
    Validate if the file size is within limits.

    Args:
        file_size: Size of the file in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = round(file_size / (1024 * 1024), 2)
        return False, f"File size ({size_mb}MB) exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, None


def generate_safe_filename(original_filename: str, preserve_extension: bool = True) -> str:
    """
    Generate a safe filename by removing special characters.

    Args:
        original_filename: Original filename
        preserve_extension: Whether to keep the file extension

    Returns:
        Safe filename
    """
    # Get name and extension
    name, ext = os.path.splitext(original_filename)

    # Remove or replace unsafe characters
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # Remove consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)

    # Remove leading/trailing underscores
    safe_name = safe_name.strip('_')

    # Ensure name is not empty
    if not safe_name:
        safe_name = f"file_{uuid.uuid4().hex[:8]}"

    # Add timestamp to make it unique
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f"{safe_name}_{timestamp}"

    if preserve_extension:
        return f"{safe_name}{ext.lower()}"
    else:
        return safe_name


def generate_storage_path(filename: str, prefix: str = "memoires") -> str:
    """
    Generate a storage path for a file.

    Args:
        filename: Name of the file
        prefix: Prefix directory (default: "memoires")

    Returns:
        Storage path like "memoires/safe_filename.pdf"
    """
    safe_name = generate_safe_filename(filename)
    return f"{prefix}/{safe_name}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB", "500 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024, 2)} KB"
    else:
        return f"{round(size_bytes / (1024 * 1024), 2)} MB"


def extract_year_from_filename(filename: str) -> Optional[int]:
    """
    Try to extract a year from the filename.

    Args:
        filename: Name of the file

    Returns:
        Year as integer if found, None otherwise
    """
    # Look for 4-digit years (1900-2099)
    pattern = r'\b(19\d{2}|20\d{2})\b'
    match = re.search(pattern, filename)

    if match:
        return int(match.group(1))

    return None


def sanitize_project_name(name: str) -> str:
    """
    Sanitize a project name for use in file paths.

    Args:
        name: Project name

    Returns:
        Sanitized name
    """
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_').lower()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].strip() + suffix


def get_file_extension(filename: str) -> str:
    """
    Get the file extension in lowercase.

    Args:
        filename: Name of the file

    Returns:
        File extension (e.g., '.pdf', '.docx')
    """
    return os.path.splitext(filename)[1].lower()


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
