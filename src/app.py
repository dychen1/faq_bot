from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.routers.answer import router as answer_router
from src.routers.get_yelp_data import router as yelp_router
from src.settings import settings
from src.utils.logger import get_queue_logger
from src.utils.middleware.auth import AuthMiddleware
from src.utils.middleware.log import LoggerMiddleware
from src.utils.state import State


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages client connections during lifespan of app, inits logger and thread pool.
    Opens them upon start up, ensuring single connection for the entire app and implicitly closes connections upon shutdown.
    """
    # Init
    logger, listener = get_queue_logger(settings.app_name)
    app.state.state = State(logger)
    yield

    # Cleanup
    app.state.state.shutdown()
    listener.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(LoggerMiddleware)
app.add_middleware(AuthMiddleware, api_key=settings.api_key)

# Mount routers
app.include_router(yelp_router)
app.include_router(answer_router)
