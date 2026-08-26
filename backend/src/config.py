# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Application configuration for Backend Reconciliation Service
"""
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings and configuration"""

    # Application
    APP_NAME: str = "Backend Reconciliation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # File Storage
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "uploads"
    # Aligned with frontend MAX_FILE_SIZE (50MB for both file types)
    MAX_PDF_SIZE: int = 50 * 1024 * 1024  # 50MB (matches frontend)
    MAX_EXCEL_SIZE: int = 50 * 1024 * 1024  # 50MB (matches frontend)
    WARNING_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB (matches frontend warning threshold)

    # File retention: 20 minutes for automatic cleanup
    # Critical security requirement: Files MUST be deleted after 20 minutes
    FILE_RETENTION_MINUTES: int = 20
    MAX_FILE_RETENTION_SECONDS: int = 20 * 60  # 1200 seconds

    # Processing
    MAX_PROCESSING_TIME: int = 30  # seconds
    SHUTDOWN_TIMEOUT: int = 10  # seconds
    MAX_CONCURRENT_REQUESTS: int = 10

    # Allowed MIME types
    ALLOWED_PDF_TYPES: list = ["application/pdf"]
    ALLOWED_EXCEL_TYPES: list = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,https://banking-reconciliationt-atmata.vercel.app"  # Comma-separated list of allowed origins

    # Authentication
    NEXTAUTH_SECRET: str = ""
    DATABASE_URL: str = ""

    # AI Structure Detection (Istikhraj e Data Ma'a AI)
    # Model id (LiteLLM-prefixed, e.g. "gemini/gemini-2.0-flash") and provider
    # API key. Never hardcoded - driven by environment variables (FR-010).
    AI_MODEL: str = ""
    AI_API_KEY: str = ""
    # Optional: dedicated API key for OpenAI Agents SDK trace export. When empty,
    # the SDK falls back to OPENAI_API_KEY / its own default.
    AI_TRACING_API_KEY: str = ""

    # Guardrail verdict layer (output validation loop)
    # Model id (LiteLLM-prefixed, e.g. "openrouter/dots-studio/dots-3-note-preview:free")
    # used for the structured LLM verdict on the agent's final structure output.
    # When empty, the guardrail uses the deterministic assessor alone.
    AI_GUARDRAIL_MODEL: str = "openrouter/dots-studio/dots-3-note-preview:free"
    AI_GUARDRAIL_API_KEY: str = ""
    AI_GUARDRAIL_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
# Create global settings instance
settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
