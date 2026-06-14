FROM node:26-bookworm-slim AS build-static

COPY ./package.json ./package-lock.json ./vite.config.js /app/

WORKDIR /app/

# Install dependencies
RUN ["npm", "ci"]

COPY ./src/static_src /app/src/static_src

RUN ["npm", "run", "build"]

FROM python:3.14-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /bin/

WORKDIR /app

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
git \
build-essential \
libjpeg62-turbo-dev \
zlib1g-dev \
libwebp-dev \
libpq-dev \
&& rm -rf /var/lib/apt/lists/*

ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_NO_SYNC=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY ./pyproject.toml ./uv.lock /app/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.14-slim-bookworm AS production

RUN useradd wagtail
WORKDIR /app
EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE="dailyplant.settings.production"

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
libjpeg62-turbo \
zlib1g \
libwebp7 \
libpq5 \
&& rm -rf /var/lib/apt/lists/*

RUN mkdir /app/static/ /app/media/
RUN chown -R wagtail:wagtail /app

COPY --from=builder /opt/venv /opt/venv

ADD --chown=wagtail:wagtail ./src /app

USER wagtail

# Copy the build JS from the previous stage
COPY --from=build-static --chown=wagtail:wagtail /app/src/static_built/ /app/static_built/

# Collect static files
RUN ["python", "manage.py", "collectstatic", "--settings", "dailyplant.settings.build"]

CMD ["gunicorn", "--bind", ":8000", "dailyplant.wsgi:application"]


FROM nginx:1.31.1-alpine AS nginx

# Copy in the build static files
COPY --from=production /app/static/ /srv/app/static/

EXPOSE 80