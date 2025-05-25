from concurrent.futures import ThreadPoolExecutor
from logging import Logger

from fastapi import Request
from google.genai import Client as GoogleClient
from httpx import AsyncClient, Limits

from src.settings import settings
from src.utils.database import db


class State:
    def __init__(self, logger: Logger):
        # Logging
        self.logger = logger

        # Settings
        self.settings = settings  # singleton

        # Clients
        self.google_client = GoogleClient(api_key=settings.google_ai_api_key)
        self.yelp_client = AsyncClient(
            limits=Limits(
                max_connections=10,
                max_keepalive_connections=1,
                keepalive_expiry=300,
            ),
            timeout=120,
        )
        self.yelp_client.headers.update(
            {"Authorization": f"Bearer {settings.yelp_api_key}", "Content-Type": "application/json"}
        )

        # Database
        self.db = db  # singleton

        # Thread pool
        self.thread_pool = ThreadPoolExecutor(max_workers=self.settings.thread_pool_size)


def get_state(req: Request) -> State:
    """Wrapper function for application state in order to return the state object with correct typing."""
    return req.app.state.state
