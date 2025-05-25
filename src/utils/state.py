import asyncio
from concurrent.futures import ThreadPoolExecutor
from logging import Logger
from typing import Any, Callable, TypeVar

from fastapi import Request
from google.genai import Client as GoogleClient
from httpx import AsyncClient, Limits

from src.settings import settings
from src.utils.database import db

T = TypeVar("T")


class State:
    def __init__(self, logger: Logger) -> None:
        # Logging
        self.logger: Logger = logger

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
        self._thread_pool: ThreadPoolExecutor | None = None

    @property
    def thread_pool(self) -> ThreadPoolExecutor:
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.settings.thread_pool_size)
        return self._thread_pool

    async def run_in_thread_pool(self, func: Callable[..., T], *args: Any) -> T:
        """
        Run a function in the application's thread pool.

        Args:
            func: The function to run
            *args: Arguments to pass to the function

        Returns:
            The function's result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args)

    def shutdown(self) -> None:
        """Safely shutdown the thread pool if it exists."""
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=True, cancel_futures=True)
            self._thread_pool = None


def get_state(req: Request) -> State:
    """Wrapper function for application state in order to return the state object with correct typing."""
    return req.app.state.state
