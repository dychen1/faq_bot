import time
from logging import Logger
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        """
        Middleware to log incoming requests and their responses.

        Args:
            app (FastAPI): FastAPI application instance.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process and log the incoming request and its response.

        Args:
            request (Request): The incoming request object.
            call_next (Callable): The next middleware or route handler.

        Returns:
            Response: The response object.
        """
        logger: Logger = request.app.state.state.logger
        start_time: float = time.time()

        request_dict: dict[str, str | float] = {"method": request.method, "path": request.url.path}

        logger.info(f"Request received: {request_dict}")
        response: Response = await call_next(request)

        response_dict: dict[str, int | float] = {
            "status": response.status_code,
            "process_time_ms": round((time.time() - start_time) * 1000, 3),
        }
        logger.info(f"Request completed: {response_dict}")
        return response
