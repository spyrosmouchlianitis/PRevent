FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VERSION=1.8.0 \
    FLASK_ENV=production \
    PYTHONPATH=/prevent

# Installing required linux packages + poetry
RUN apk update && \
    apk add gcc libpq-dev curl && \
    rm -rf /var/cache/apk/* && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    # Default Alpine PATH doesn't include /root/.local/bin/
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /prevent

# Copying the source code of prevent to image
COPY ./src /prevent/src
COPY ./setup /prevent/setup
COPY ./pyproject.toml /prevent/pyproject.toml

# Install project dependencies with Poetry
RUN poetry install --no-interaction --only main

EXPOSE 8080

# Run setup.py from the ./setup directory
RUN poetry run python -m setup.setup_container

# Run the prevent application
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "src.app:app"]
