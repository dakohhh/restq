# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

# Set build arguments and environment variables
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Install system build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pkg-config \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/poetry \
    poetry config installer.max-workers 10 && \
    poetry install --no-interaction --no-root --only docs && \
    poetry export -f requirements.txt --output requirements.txt

COPY docs docs
COPY mkdocs.yml mkdocs.yml

RUN mkdocs build

# Next, we create a new stage using the nginx:latest image.
FROM nginx:latest as runner

# We copy the default.conf.template file from the host machine into the container at /etc/nginx/templates/default.conf.template.
COPY ./docs/default.conf.template /etc/nginx/templates/default.conf.template

# We copy the built app from the build stage into the container at /var/www/html.
COPY --from=builder /app/site /var/www/html

# We expose port 80 for the nginx server to listen on.
EXPOSE 80

# Finally, we set the default command to start the nginx server.
CMD ["nginx", "-g", "daemon off;"]
