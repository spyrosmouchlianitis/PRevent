FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VERSION=1.8.0 \
    FLASK_ENV=production

# Installing required linux packages + poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/* && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry #todo is this required?

# Copying the source code of prevent to image
COPY ../setup ../src ../pyproject.toml /

# Install project dependencies with Poetry
RUN poetry install --no-interaction --no-dev

EXPOSE 8080

# Run setup.py from the ./setup directory
RUN python -m setup.setup

# Run the prevent application
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "src.app:app"]