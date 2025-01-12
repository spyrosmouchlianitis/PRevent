# A lightweight official Python base image for build stage
FROM python:3.11-slim AS build

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VERSION=1.8.0

# Install system dependencies required for your app and pip package installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set the working directory to /pr-event inside the container
WORKDIR /pr-event

# Copy only the necessary files to install dependencies first
COPY pyproject.toml poetry.lock /pr-event/

# Install project dependencies with Poetry
RUN poetry install --no-interaction --no-dev

# A smaller, cleaner runtime image
FROM python:3.11-slim AS runtime

# Copy all necessary files from the build stage
COPY --from=build /pr-event .

# Expose the port the app will run on
EXPOSE 8080

# Set the environment to production
ENV FLASK_ENV=production

# Run setup.py from the ./setup directory
RUN python /pr-event/setup/setup.py

# Change CMD to use Gunicorn through Poetry
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "src.app:app"]
