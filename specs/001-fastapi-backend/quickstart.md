# Quick Start Guide: Backend API Implementation

**Feature**: `001-fastapi-backend`  
**Date**: 2025-06-18  
**Phase**: Phase 1 - Design & Contracts

## Overview

This guide provides step-by-step instructions for implementing the backend API service for bank reconciliation. It covers environment setup, project structure, and implementation priorities.

## Prerequisites

### Required Software
- **Python 3.11+**: Main programming language
- **Git**: Version control (already initialized)
- **Code Editor**: VS Code or similar with Python support
- **Java Runtime Environment (JRE)**: Required by Tabula-py

### System Requirements
- **Windows 10 Pro** (or compatible environment)
- **Disk Space**: 500MB for dependencies + temporary file storage
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Network**: Local development only (no internet required for operation)

## Project Setup

### 1. Backend Directory Structure

Create the backend directory structure:

```bash
# Navigate to project root
cd "D:\Agentic_AI\Bank Reconciliation System"

# Create backend directories
mkdir -p backend/src/{models,services,api,utils}
mkdir -p backend/tests/{contract,integration,unit}
mkdir -p backend/uploads

# Create Python package markers
touch backend/src/__init__.py
touch backend/src/models/__init__.py
touch backend/src/services/__init__.py
touch backend/src/api/__init__.py
touch backend/src/utils/__init__.py
touch backend/tests/__init__.py
touch backend/tests/contract/__init__.py
touch backend/tests/integration/__init__.py
touch backend/tests/unit/__init__.py
```

### 2. Python Dependencies

Create `backend/requirements.txt`:

```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Data Processing
pandas==2.1.4
openpyxl==3.3.0
tabula-py==2.9.0

# Utilities
python-dateutil==2.8.2
pydantic==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
httpx==0.25.2

# Development
black==23.12.1
flake8==6.1.0
mypy==1.7.1
```

### 3. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Java for Tabula-py (if not already installed)
# Tabula-py requires Java Runtime Environment
```

### 4. Initial Configuration

Create `backend/src/config.py`:

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Application configuration for Backend Reconciliation Service
"""
import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings"""
    
    # Application
    APP_NAME: str = "Backend Reconciliation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # File Storage
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "uploads"
    MAX_PDF_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_EXCEL_SIZE: int = 5 * 1024 * 1024  # 5MB
    FILE_RETENTION_HOURS: int = 1
    
    # Processing
    MAX_PROCESSING_TIME: int = 30  # seconds
    SHUTDOWN_TIMEOUT: int = 10  # seconds
    
    # Allowed MIME types
    ALLOWED_PDF_TYPES: list = ["application/pdf"]
    ALLOWED_EXCEL_TYPES: list = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()

# وَإِنَّ اللَّهَ لَهُو خَيْرُ الرَّازِقِينَ
```

## Implementation Priority

### Phase 1: Core Infrastructure (Days 1-2)

#### 1.1 Basic FastAPI Application
**File**: `backend/src/main.py`

```python
# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
import uvicorn

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for bank reconciliation processing"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": "2025-06-18T10:30:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
```

**Testing**:
```bash
# Run the application
python -m src.main

# Test health endpoint
curl http://localhost:8000/health
```

#### 1.2 File Upload Models
**File**: `backend/src/models/file_models.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class FileValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_SIZE = "invalid_size"
    CORRUPTED = "corrupted"
    EMPTY = "empty"

class BankStatementUpload(BaseModel):
    file_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    storage_path: str
    validation_status: FileValidationStatus = FileValidationStatus.PENDING

class CompanyDataUpload(BaseModel):
    file_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    storage_path: str
    validation_status: FileValidationStatus = FileValidationStatus.PENDING
```

### Phase 2: File Processing Services (Days 3-5)

#### 2.1 File Storage Service
**File**: `backend/src/services/file_storage_service.py`

**Key Features**:
- Upload file validation
- Temporary file storage
- File cleanup management
- Secure file handling

#### 2.2 PDF Processing Service  
**File**: `backend/src/services/pdf_service.py`

**Key Features**:
- PDF table extraction using Tabula-py
- Multiple extraction modes (lattice, stream)
- Error handling for corrupted PDFs
- Metadata extraction

#### 2.3 Excel Processing Service
**File**: `backend/src/services/excel_service.py`

**Key Features**:
- Excel file parsing using Pandas
- Column validation based on user input
- Data type conversion
- Error handling for malformed files

### Phase 3: API Endpoints (Days 6-8)

#### 3.1 Main Processing Endpoint
**File**: `backend/src/api/routes.py`

**Implementation**:
```python
@app.post("/karwai")
async def process_reconciliation(
    bankStatement: UploadFile,
    companyData: UploadFile,
    formatType: str,
    transactionDateColumn: str,
    transactionDetailsColumn: str,
    debitPlusCreditColumn: Optional[str] = None,
    debitColumn: Optional[str] = None,
    creditColumn: Optional[str] = None
):
    """Main reconciliation processing endpoint"""
    # Implementation steps:
    # 1. Validate file sizes and formats
    # 2. Store files temporarily
    # 3. Extract data from PDF and Excel
    # 4. Process reconciliation logic
    # 5. Return results
    pass
```

### Phase 4: Reconciliation Logic (Days 9-12)

#### 4.1 Core Reconciliation Service
**File**: `backend/src/services/reconciliation_service.py`

**Key Features**:
- Transaction matching algorithm
- Discrepancy detection
- Confidence scoring
- Result formatting

### Phase 5: Testing and Deployment (Days 13-15)

#### 5.1 Unit Tests
Create comprehensive unit tests for each service

#### 5.2 Integration Tests
Test end-to-end reconciliation workflows

#### 5.3 Performance Testing
Verify performance requirements are met

#### 5.4 Frontend Integration
Connect with existing Next.js frontend

## Development Workflow

### 1. Setup Development Environment

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Development Server

```bash
# Start the development server
python -m src.main

# Or use uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Interactive API documentation
# Open browser to http://localhost:8000/docs
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=src tests/
```

### 5. Code Quality Checks

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Configuration Management

### Environment Variables

Create `.env` file in backend directory:

```env
# Application Settings
DEBUG=true
APP_NAME=Backend Reconciliation API
APP_VERSION=1.0.0

# Server Settings
HOST=0.0.0.0
PORT=8000

# File Storage
UPLOAD_DIR=./uploads
MAX_PDF_SIZE=10485760
MAX_EXCEL_SIZE=5242880
FILE_RETENTION_HOURS=1

# Processing
MAX_PROCESSING_TIME=30
SHUTDOWN_TIMEOUT=10

# Logging
LOG_LEVEL=INFO
```

Update `backend/src/config.py` to read from environment:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Debugging Tips

### 1. Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Test File Processing Manually

```python
# Test PDF extraction
import tabula

df = tabula.read_pdf("bank_statement.pdf", pages="all")
print(df)

# Test Excel parsing
import pandas as pd

df = pd.read_excel("company_data.xlsx")
print(df.head())
```

### 3. Monitor File Storage

```bash
# Check upload directory
ls -la backend/uploads/

# Clean up manually if needed
rm -rf backend/uploads/*
```

## Common Issues and Solutions

### Issue 1: Tabula-py Java Error
**Problem**: Tabula-py requires Java but can't find it  
**Solution**: Install Java Runtime Environment and ensure it's in PATH

### Issue 2: File Upload Timeout
**Problem**: Large files cause timeout during upload  
**Solution**: Increase timeout in uvicorn configuration or client settings

### Issue 3: Memory Issues
**Problem**: Processing large files consumes too much memory  
**Solution**: Implement streaming processing and increase memory limits

### Issue 4: Pandas Excel Reading Errors
**Problem**: Pandas fails to read certain Excel formats  
**Solution**: Try different engines (`openpyxl`, `xlrd`) or specify parameters

## Performance Optimization

### 1. Async Operations
Use async/await throughout for non-blocking operations

### 2. File Streaming
Use streaming for large file uploads instead of loading entirely into memory

### 3. Caching
Cache repetitive operations like file type detection

### 4. Connection Pooling
Reuse connections for external services

## Security Considerations

### 1. Input Validation
Validate all file inputs, sizes, and formats

### 2. Path Traversal Prevention
Secure file naming to prevent path traversal attacks

### 3. Resource Limits
Implement rate limiting and resource quotas

### 4. Error Messages
Don't expose sensitive information in error messages

## Frontend Integration

### Update Frontend API Client

The frontend already has the API call structure (see `frontend/src/components/upload/UploadForm.tsx`). Update the submit handler:

```typescript
// Update the handleSubmit function to point to real backend
const response = await fetch('http://localhost:8000/karwai', {
  method: 'POST',
  body: formData
});

const results = await response.json();
```

### Test Integration

```bash
# Start backend
cd backend
python -m src.main

# Start frontend (new terminal)
cd frontend
npm run dev

# Open browser to http://localhost:3000/upload
```

## Next Steps

1. **Complete Implementation**: Follow the implementation priorities above
2. **Add Tests**: Create comprehensive test coverage
3. **Performance Testing**: Verify performance requirements
4. **Frontend Integration**: Connect with existing frontend
5. **Documentation**: Add inline code documentation
6. **Deployment**: Prepare for production deployment

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pandas Documentation**: https://pandas.pydata.org/docs/
- **Tabula-py Documentation**: https://tabula-py.readthedocs.io/
- **Python Async Programming**: https://docs.python.org/3/library/asyncio.html

## Support

For implementation questions or issues:
1. Check the API contract in `contracts/api-contract.md`
2. Review data model in `data-model.md`
3. Consult research findings in `research.md`
4. Refer to this quick start guide

---

**وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ**