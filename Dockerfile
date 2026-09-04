FROM python:3.13-slim

WORKDIR /app

# System deps needed for psycopg2 and building some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

EXPOSE 8000

# Run migrations, then start the app.
# $PORT is set automatically by Railway/Render; falls back to 8000 locally.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}