# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy 

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry

# Poetry יותקן את התלויות שכבר בפנים
RUN poetry install --no-root

COPY . .

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1