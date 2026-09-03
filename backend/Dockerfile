# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
# Backend production image
# Use uv's official slim Python image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Runtime uploads live under /app/data/uploads (writable, ephemeral).
# Not part of the image layer — mount a volume here in production.
ENV UPLOAD_DIR=/app/data/uploads

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY ./pyproject.toml ./uv.lock /app/
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY ./src /app/src

# Create non-root user and writable data dir
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data/uploads \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Production: no --reload
CMD ["uv", "run", "--no-sync", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
