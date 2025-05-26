#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if uv is installed
if ! command_exists uv; then
    echo "uv is not installed. Please install uv from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    echo "Creating virtual environment and installing dependencies..."
    uv .venv
    uv sync
fi

# Source environment variables for app port
source "${SCRIPT_DIR}/src/env/.env"

# Run the FastAPI application
uv run fastapi dev src/app.py --port ${APP_PORT:-8001} --reload