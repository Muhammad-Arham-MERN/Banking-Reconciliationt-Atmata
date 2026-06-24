# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Input validation utilities
File validation, security checks, and data sanitization
"""
import re
import os
from typing import Optional, List, Tuple
from src.config import settings

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for security issues
    Consistency Pattern: Must prevent path traversal attacks

    Args:
        filename: Original filename from upload

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is empty"

    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Filename contains path traversal characters"

    # Check for null bytes
    if "\x00" in filename:
        return False, "Filename contains null bytes"

    # Check filename length
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"

    # Check for valid characters (letters, numbers, spaces, underscores, hyphens, dots)
    if not re.match(r'^[a-zA-Z0-9_\-\.\s]+$', filename):
        return False, "Filename contains invalid characters"

    return True, None

def validate_file_size(file_size: int, max_size: int) -> Tuple[bool, Optional[str]]:
    """
    Validate file size against limits
    Consistency Pattern: Must match frontend file size validation

    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size == 0:
        return False, "File is empty"

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"File size {actual_mb:.1f}MB exceeds maximum {max_mb:.0f}MB"

    return True, None

def validate_mime_type(file_type: str, allowed_types: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate MIME type against allowed types
    Consistency Pattern: Must match frontend MIME type validation

    Args:
        file_type: MIME type from file upload
        allowed_types: List of allowed MIME types

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_type:
        return False, "MIME type is empty"

    if file_type not in allowed_types:
        return False, f"MIME type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}"

    return True, None

def validate_file_extension(filename: str, allowed_extensions: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension against allowed extensions
    Consistency Pattern: Must match frontend extension validation

    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.xlsx'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is empty"

    # Get file extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in allowed_extensions:
        return False, f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"

    return True, None

def validate_pdf_file(file_size: int, file_type: str, filename: str) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate PDF file against all constraints
    Consistency Pattern: Must match frontend PDF validation rules

    Args:
        file_size: Size of file in bytes
        file_type: MIME type from upload
        filename: Original filename

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Validate filename
    filename_valid, filename_error = validate_filename(filename)
    if not filename_valid:
        errors.append(filename_error)

    # Validate file size
    size_valid, size_error = validate_file_size(file_size, settings.MAX_PDF_SIZE)
    if not size_valid:
        errors.append(size_error)

    # Validate MIME type
    mime_valid, mime_error = validate_mime_type(file_type, settings.ALLOWED_PDF_TYPES)
    if not mime_valid:
        errors.append(mime_error)

    # Validate file extension
    ext_valid, ext_error = validate_file_extension(filename, ['.pdf'])
    if not ext_valid:
        errors.append(ext_error)

    # Check for large file warning
    if file_size > settings.WARNING_FILE_SIZE:
        errors.append(f"Large file detected (>10MB). Upload may take longer.")

    return len(errors) == 0, (errors if errors else None)

def validate_excel_file(file_size: int, file_type: str, filename: str) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate Excel file against all constraints
    Consistency Pattern: Must match frontend Excel validation rules

    Args:
        file_size: Size of file in bytes
        file_type: MIME type from upload
        filename: Original filename

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Validate filename
    filename_valid, filename_error = validate_filename(filename)
    if not filename_valid:
        errors.append(filename_error)

    # Validate file size
    size_valid, size_error = validate_file_size(file_size, settings.MAX_EXCEL_SIZE)
    if not size_valid:
        errors.append(size_error)

    # Validate MIME type
    mime_valid, mime_error = validate_mime_type(file_type, settings.ALLOWED_EXCEL_TYPES)
    if not mime_valid:
        errors.append(mime_error)

    # Validate file extension
    ext_valid, ext_error = validate_file_extension(filename, ['.xlsx', '.xls'])
    if not ext_valid:
        errors.append(ext_error)

    # Check for large file warning
    if file_size > settings.WARNING_FILE_SIZE:
        errors.append(f"Large file detected (>10MB). Upload may take longer.")

    return len(errors) == 0, (errors if errors else None)

def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Sanitize user input for security
    Removes dangerous characters and limits length

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Trim and limit length
    sanitized = sanitized.strip()[:max_length]

    return sanitized

def validate_column_name(column_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate column name for database/spreadsheet operations
    Consistency Pattern: Must match frontend column name validation

    Args:
        column_name: Column name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not column_name or not column_name.strip():
        return False, "Column name is empty"

    sanitized = sanitize_input(column_name, max_length=100)

    if not sanitized:
        return False, "Column name is empty after sanitization"

    # Check for valid characters (letters, numbers, spaces, underscores, hyphens)
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', sanitized):
        return False, "Column name contains invalid characters"

    return True, None

def validate_format_type(format_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate format type value
    Consistency Pattern: Must match frontend format type validation

    Args:
        format_type: Format type to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_types = ["debit-plus-credit", "debit-pipe-credit"]

    if format_type not in valid_types:
        return False, f"Invalid format type. Must be one of: {', '.join(valid_types)}"

    return True, None

def validate_column_mapping_configuration(config: dict) -> Tuple[bool, Optional[dict]]:
    """
    Validate complete column mapping configuration
    Consistency Pattern: Must match frontend configuration validation

    Args:
        config: Column mapping configuration dictionary

    Returns:
        Tuple of (is_valid, errors_dict)
    """
    errors = {}

    format_type = config.get("format_type")
    if not format_type:
        errors["format_type"] = "Format type is required"
        return False, errors

    # Validate format type
    format_valid, format_error = validate_format_type(format_type)
    if not format_valid:
        errors["format_type"] = format_error
        return False, errors

    # Validate common fields
    date_column = config.get("transactionDateColumn")
    if not date_column:
        errors["transactionDateColumn"] = "Transaction date column is required"
    else:
        date_valid, date_error = validate_column_name(date_column)
        if not date_valid:
            errors["transactionDateColumn"] = date_error

    details_column = config.get("transactionDetailsColumn")
    if not details_column:
        errors["transactionDetailsColumn"] = "Transaction details column is required"
    else:
        details_valid, details_error = validate_column_name(details_column)
        if not details_valid:
            errors["transactionDetailsColumn"] = details_error

    # Validate format-specific fields
    if format_type == "debit-plus-credit":
        debit_credit_column = config.get("debitPlusCreditColumn")
        if not debit_credit_column:
            errors["debitPlusCreditColumn"] = "Debit+Credit column is required"
        else:
            column_valid, column_error = validate_column_name(debit_credit_column)
            if not column_valid:
                errors["debitPlusCreditColumn"] = column_error

    elif format_type == "debit-pipe-credit":
        debit_column = config.get("debitColumn")
        if not debit_column:
            errors["debitColumn"] = "Debit column is required"
        else:
            column_valid, column_error = validate_column_name(debit_column)
            if not column_valid:
                errors["debitColumn"] = column_error

        credit_column = config.get("creditColumn")
        if not credit_column:
            errors["creditColumn"] = "Credit column is required"
        else:
            column_valid, column_error = validate_column_name(credit_column)
            if not column_valid:
                errors["creditColumn"] = column_error

    return len(errors) == 0, (errors if errors else None)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ