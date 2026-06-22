#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

USE_CHINA_MIRRORS=0
WITH_MODELS=0
NOLOGIN=0
SKIP_BUILD=0

usage() {
  cat <<'EOF'
Usage: ./scripts/docker-deploy.sh [options]

Build and start Auto-Slides with Docker Compose.

Options:
  --with-models  Download the optional Marker/Surya models into the Docker volume.
  --nologin      Enable local single-user automatic login mode.
  --skip-build   Reuse the existing local image instead of rebuilding it.
  --china        Use the China mainland mirror configuration.
  -h, --help     Show this help message.
EOF
}

while (($#)); do
  case "$1" in
    --with-models)
      WITH_MODELS=1
      ;;
    --nologin)
      NOLOGIN=1
      ;;
    --skip-build)
      SKIP_BUILD=1
      ;;
    --china)
      USE_CHINA_MIRRORS=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Engine or Docker Desktop first." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "The Docker Compose plugin is required: https://docs.docker.com/compose/install/" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example."
  echo "Edit .env, add a valid DEEPSEEK_API_KEY or OPENROUTER_API_KEY, then run this command again."
  exit 2
fi

read_env_value() {
  local key="$1"
  sed -n "s/^${key}=//p" .env | tail -n 1 | tr -d '\r'
}

deepseek_key="$(read_env_value DEEPSEEK_API_KEY)"
openrouter_key="$(read_env_value OPENROUTER_API_KEY)"
openai_key="$(read_env_value OPENAI_API_KEY)"
if [[ -z "${openrouter_key}" && -z "${openai_key}" && ( -z "${deepseek_key}" || "${deepseek_key}" == your_* ) ]]; then
  echo "No usable LLM API key was found in .env." >&2
  echo "Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY before deploying." >&2
  exit 2
fi

admin_password="$(read_env_value AUTOSLIDES_ADMIN_PASSWORD)"
user_password="$(read_env_value AUTOSLIDES_USER_PASSWORD)"
if [[ -z "${admin_password}" || -z "${user_password}" || "${admin_password}" == "change-me" || "${user_password}" == "change-me" ]]; then
  echo "Replace the default AUTOSLIDES_ADMIN_PASSWORD and AUTOSLIDES_USER_PASSWORD in .env first." >&2
  exit 2
fi

if [[ ! -f backend/settings.toml ]]; then
  cp backend/settings.example.toml backend/settings.toml
  chmod 600 backend/settings.toml
  echo "Created backend/settings.toml for optional --nologin mode."
fi

compose_args=(-f docker-compose.yml)
if ((USE_CHINA_MIRRORS)); then
  compose_args+=(-f docker-compose.cn.yml)
  echo "Using China mainland container and package mirrors."
fi

if ((NOLOGIN)); then
  export AUTOSLIDES_NOLOGIN=1
fi

if ((!SKIP_BUILD)); then
  docker compose "${compose_args[@]}" build
fi

if ((WITH_MODELS)); then
  echo "Downloading Marker/Surya models into the persistent Docker volume..."
  docker compose "${compose_args[@]}" run --rm app python scripts/download_models.py
fi

docker compose "${compose_args[@]}" up -d

port="${AUTOSLIDES_PORT:-8000}"
echo
echo "Auto-Slides is starting at http://localhost:${port}"
echo "View logs with: docker compose ${compose_args[*]} logs -f app"
echo "Stop with:      docker compose ${compose_args[*]} down"
