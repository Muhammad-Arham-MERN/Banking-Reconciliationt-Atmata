# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
# Use uv's official slim Python image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY ./pyproject.toml ./uv.lock /app/
RUN uv sync --frozen --no-dev

# Copy application source
COPY ./src /app/src

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
