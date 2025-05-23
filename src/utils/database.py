from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings


class DatabaseUtilities:
    def __init__(self, dialect: str = "sqlite+aiosqlite") -> None:
        """Database class to interact with SQLite database."""
        db_path: Path = Path(f"./data/{settings.database_url.split('/')[-1]}")
        self.database_url: str = f"{dialect}:///{db_path.absolute()}"

        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},  # Allow multiple threads to access the database
        )

        self.session_maker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def create_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Creates an async database session context manager that handles commit, rollback, and cleanup operations.

        This method should be used in an async context manager.
        The session will automatically commit on successful completion or rollback on error.

        Returns:
            AsyncGenerator[AsyncSession, None]: A database session wrapped in an async context manager

        Example for manual session management:
            async with db_utils.create_session() as session:
                user = User(name="denis")
                session.add(user)
                await session.commit()
                # Session automatically closes when context exits

        Raises:
            Any exceptions that occur during database operations

        Note:
            Only use this function when you want to start a new transaction manually!!
        """
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates an async session generator for FastAPI dependency injection.

    This method is designed to be used with FastAPI's dependency injection system.
    It wraps create_session() to provide automatic session management in API endpoints.

    Returns:
        Generator[Session, None, None]: A database session generator for dependency injection

    Example:
        @app.get("/users/{user_id}")
        def get_user(
            user_id: int,
            db: Session = Depends(db_utils.get_session)
        ):
            return db.query(User).filter(User.id == user_id).first()

    Note:
        This method should be used as a dependency in FastAPI route functions.
        If downstream functions need to use the same transaction, the session should be passed as an argument.
    """
    async with db.create_session() as session:
        yield session


# Singleton instance for entire application
db = DatabaseUtilities()
