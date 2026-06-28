FROM python:3.13-slim as base

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements/base.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Development stage
FROM base as development
COPY requirements/dev.txt ./dev-requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
COPY requirements/prod.txt ./prod-requirements.txt
RUN pip install --no-cache-dir -r prod-requirements.txt
COPY . .
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
