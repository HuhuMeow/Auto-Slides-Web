# syntax=docker/dockerfile:1.7

ARG NODE_IMAGE=docker.io/library/node:20-bookworm-slim
ARG PYTHON_IMAGE=docker.io/library/python:3.11-slim-bookworm

FROM ${NODE_IMAGE} AS frontend-builder

ARG NPM_REGISTRY=https://registry.npmjs.org
WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry "${NPM_REGISTRY}" \
    && npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


FROM ${PYTHON_IMAGE} AS python-builder

ARG DEBIAN_MIRROR=http://deb.debian.org/debian
ARG DEBIAN_SECURITY_MIRROR=http://deb.debian.org/debian-security
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install -r requirements.txt


FROM ${PYTHON_IMAGE} AS runtime

ARG DEBIAN_MIRROR=http://deb.debian.org/debian
ARG DEBIAN_SECURITY_MIRROR=http://deb.debian.org/debian-security

ENV PATH=/opt/venv/bin:${PATH} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AUTOSLIDES_RUNTIME_DIR=/app/.runtime \
    AUTOSLIDES_DATA_DIR=/app/.runtime/data \
    AUTOSLIDES_MARKER_MODEL_DIR=/app/.runtime/models

RUN sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      fonts-noto-cjk \
      libgl1 \
      libglib2.0-0 \
      libgomp1 \
      libmagic1 \
      poppler-utils \
      texlive-fonts-recommended \
      texlive-lang-chinese \
      texlive-latex-base \
      texlive-latex-extra \
      texlive-latex-recommended \
      texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=python-builder /opt/venv /opt/venv
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY static/ ./static/
COPY requirements.txt ./
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist/

RUN mkdir -p /app/.runtime/data /app/.runtime/models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/auth/me', timeout=4)" || exit 1

CMD ["python", "-m", "backend", "--host", "0.0.0.0", "--port", "8000"]
