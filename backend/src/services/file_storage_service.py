# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
File Storage Service
Handles temporary file storage, validation, and cleanup operations
"""
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
import logging

from src.config import settings
from src.models.file_models import (
    BankStatementUpload, CompanyDataUpload, FileValidationStatus
)

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class FileStorageService:
    """
    Service for managing temporary file storage operations
    Handles file validation, storage, and automatic cleanup
    """

    def __init__(self):
        """Initialize file storage service"""
        self.upload_dir = settings.UPLOAD_DIR
        self.max_pdf_size = settings.MAX_PDF_SIZE
        self.max_excel_size = settings.MAX_EXCEL_SIZE
        self.file_retention_minutes = settings.FILE_RETENTION_MINUTES
        self._file_registry: Dict[str, Dict[str, Any]] = {}  # Track uploaded files

    def _generate_file_id(self, filename: str) -> str:
        """Generate unique file identifier"""
        return f"file-{uuid.uuid4().hex}-{filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks
        Security: Removes path components and suspicious characters
        """
        # Remove any directory paths
        clean_name = os.path.basename(filename)

        # Remove potentially dangerous characters
        dangerous_chars = ['..', '\\', '/', '\0', '\n', '\r']
        for char in dangerous_chars:
            clean_name = clean_name.replace(char, '')

        # Limit filename length
        if len(clean_name) > 255:
            clean_name = clean_name[:255]

        return clean_name or "unnamed_file"

    def _validate_file_size(self, file: UploadFile, max_size: int) -> None:
        """Validate file size against maximum allowed size"""
        try:
            # Seek to end to get file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Seek back to beginning

            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": "file_too_large",
                        "message": "File size exceeds maximum allowed size",
                        "details": {
                            "field": file.filename,
                            "max_size_mb": max_size / (1024 * 1024),
                            "actual_size_mb": file_size / (1024 * 1024)
                        }
                    }
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Error validating file size: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "processing_error", "message": "Error validating file size"}
            )

    def _validate_mime_type(self, file: UploadFile, allowed_types: list) -> None:
        """Validate file MIME type"""
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_file",
                    "message": "Invalid file format",
                    "details": {
                        "field": file.filename,
                        "expected_types": allowed_types,
                        "actual_type": file.content_type
                    }
                }
            )

    async def store_bank_statement(self, file: UploadFile) -> BankStatementUpload:
        """
        Store uploaded bank statement PDF file
        Validates file size, format, and stores securely
        """
        try:
            # Validate file size
            self._validate_file_size(file, self.max_pdf_size)

            # Validate MIME type
            self._validate_mime_type(file, settings.ALLOWED_PDF_TYPES)

            # Generate file ID and sanitize filename
            file_id = self._generate_file_id(file.filename or "bank_statement.pdf")
            safe_filename = self._sanitize_filename(file.filename or "bank_statement.pdf")
            storage_path = self.upload_dir / f"{file_id}.pdf"

            # Save file to disk
            with open(storage_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            # Create file upload model
            file_upload = BankStatementUpload(
                file_id=file_id,
                original_filename=safe_filename,
                file_size=len(content),
                mime_type=file.content_type or "application/pdf",
                storage_path=str(storage_path),
                validation_status=FileValidationStatus.VALID
            )

            # Register file in cleanup registry
            self._register_file(file_id, str(storage_path), "pdf")

            logger.info(f"Stored bank statement: {file_id} ({len(content)} bytes)")
            return file_upload

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error storing bank statement: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "processing_error", "message": f"Error storing file: {str(e)}"}
            )

    async def store_company_data(self, file: UploadFile) -> CompanyDataUpload:
        """
        Store uploaded company data Excel file
        Validates file size, format, and stores securely
        """
        try:
            # Validate file size
            self._validate_file_size(file, self.max_excel_size)

            # Validate MIME type
            self._validate_mime_type(file, settings.ALLOWED_EXCEL_TYPES)

            # Generate file ID and sanitize filename
            file_id = self._generate_file_id(file.filename or "company_data.xlsx")
            safe_filename = self._sanitize_filename(file.filename or "company_data.xlsx")

            # Determine extension from MIME type
            ext = '.xlsx' if 'openxmlformats' in file.content_type else '.xls'
            storage_path = self.upload_dir / f"{file_id}{ext}"

            # Save file to disk
            with open(storage_path, 'wb') as f:
                content = await file.read()
                f.write(content)

            # Create file upload model
            file_upload = CompanyDataUpload(
                file_id=file_id,
                original_filename=safe_filename,
                file_size=len(content),
                mime_type=file.content_type,
                storage_path=str(storage_path),
                validation_status=FileValidationStatus.VALID
            )

            # Register file in cleanup registry
            self._register_file(file_id, str(storage_path), "excel")

            logger.info(f"Stored company data: {file_id} ({len(content)} bytes)")
            return file_upload

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error storing company data: {e}")
            raise HTTPException(
                status_code=500,
                detail={"error": "processing_error", "message": f"Error storing file: {str(e)}"}
            )

    def _register_file(self, file_id: str, storage_path: str, file_type: str) -> None:
        """Register file in cleanup registry"""
        self._file_registry[file_id] = {
            "storage_path": storage_path,
            "file_type": file_type,
            "upload_time": datetime.now()
        }

    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from storage
        Returns True if file was deleted, False otherwise
        """
        try:
            if file_id not in self._file_registry:
                logger.warning(f"File {file_id} not found in registry")
                return False

            file_info = self._file_registry[file_id]
            storage_path = Path(file_info["storage_path"])

            if storage_path.exists():
                os.remove(storage_path)
                logger.info(f"Deleted file: {file_id}")
                del self._file_registry[file_id]
                return True
            else:
                logger.warning(f"File not found on disk: {storage_path}")
                del self._file_registry[file_id]
                return False

        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False

    def cleanup_old_files(self, max_age_minutes: Optional[int] = None) -> int:
        """
        Clean up files older than specified age
        Returns number of files deleted
        """
        try:
            age_limit = max_age_minutes or self.file_retention_minutes
            cutoff_time = datetime.now() - timedelta(minutes=age_limit)

            files_to_delete = []
            for file_id, file_info in self._file_registry.items():
                upload_time = file_info["upload_time"]
                if upload_time < cutoff_time:
                    files_to_delete.append(file_id)

            deleted_count = 0
            for file_id in files_to_delete:
                if self.delete_file(file_id):
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files (older than {age_limit} minutes)")

            return deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def cleanup_all_files(self) -> int:
        """
        Delete ALL files from storage
        Critical security operation for shutdown
        Returns number of files deleted
        """
        try:
            all_file_ids = list(self._file_registry.keys())
            deleted_count = 0

            for file_id in all_file_ids:
                if self.delete_file(file_id):
                    deleted_count += 1

            logger.info(f"Cleaned up ALL {deleted_count} files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during full cleanup: {e}")
            return 0

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stored file"""
        return self._file_registry.get(file_id)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_files = len(self._file_registry)
        total_size = 0

        for file_info in self._file_registry.values():
            storage_path = Path(file_info["storage_path"])
            if storage_path.exists():
                total_size += storage_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "upload_dir": str(self.upload_dir)
        }

# Global service instance
file_storage_service = FileStorageService()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ