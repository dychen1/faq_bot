SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${SCRIPT_DIR}/src/env/.env"
uv run fastapi dev src/app.py --port ${APP_PORT:-8001} --reload