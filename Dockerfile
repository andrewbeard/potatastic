FROM python:3.13-alpine AS base

ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

RUN adduser --gecos "" --disabled-password -s /sbin/nologin --home /tmp --uid 1000 potatastic && \
    mkdir -p /app
RUN mkdir -p /app
WORKDIR /app
COPY src /app/src


FROM base AS dev
COPY pyproject.toml uv.lock /app/
RUN apk --no-cache add uv && \
    uv sync --dev
CMD ["ash"]


FROM base AS prod
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    apk --no-cache -U upgrade && \
    apk add --no-cache uv && \
    uv sync --locked --compile --link-mode=copy --no-dev && \
    apk --no-cache del uv

USER potatastic
ENV PYTHONOPTIMIZE=1
CMD ["python", "src/potatastic.py"]