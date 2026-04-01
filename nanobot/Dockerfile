# Adapted from https://github.com/astral-sh/uv-docker-example/blob/fa761744819c05f4ce207bde1f0a396f6be3915f/multistage.Dockerfile
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy nanobot's pyproject.toml first for better layer caching
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY . /app/nanobot

# Copy mcp directory for installing mcp-lms
COPY --from=workspace mcp /app/mcp

# Copy nanobot-websocket-channel for installing webchat packages
COPY --from=workspace nanobot-websocket-channel /app/nanobot-websocket-channel

# Change to nanobot directory and install all dependencies directly
WORKDIR /app/nanobot
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install \
        /app/nanobot-websocket-channel/mcp-webchat \
        /app/nanobot-websocket-channel/nanobot-webchat \
        /app/mcp/mcp-lms \
        /app/mcp/mcp-obs \
        "nanobot-ai>=0.1.4.post6"

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Make sure we use UTF-8 encoding
ENV LANG=C.UTF-8

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/nanobot/.venv/bin:$PATH"

# Use the appuser to run our application (or root if APP_UID=0)
ARG APP_UID=999                                                                                                                                                                    
ARG APP_GID=999                                                                                                                                                                    
USER ${APP_UID}:${APP_GID} 

# Use `/app/nanobot` as the working directory
WORKDIR /app/nanobot

# Run the nanobot gateway via entrypoint
CMD ["python", "/app/nanobot/entrypoint.py"]
