import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src import ENV_PATH


class Settings(BaseSettings):
    """
    Settings for the application.
    Loads environment variables from the system environment first, then from the .env file for missing variables.
    All settings are frozen (immutable) after initialization via model_config.
    """

    # API Keys
    api_key: str = Field(alias="API_KEY")
    yelp_api_key: str = Field(alias="YELP_API_KEY")
    google_ai_api_key: str = Field(alias="GOOGLE_AI_API_KEY")

    # App Settings
    app_name: str = Field(alias="APP_NAME")
    app_port: int = Field(alias="APP_PORT")
    thread_pool_size: int = Field(
        alias="APP_THREAD_POOL_SIZE",
        default=min(16, os.cpu_count() or 1 + 2),
        description="Number of worker threads in the thread pool for application. Keep in mind 1 thread is used for queue logger.",
    )

    # Yelp Settings
    yelp_base_url: str = Field(alias="YELP_BASE_URL")

    # Database Settings
    database_url: str = Field(alias="DATABASE_URL")

    # Model settings
    chat_model: str = Field(alias="CHAT_MODEL")
    chat_temperature: float = Field(alias="CHAT_TEMPERATURE", default=0.0)
    validation_model: str = Field(alias="VALIDATION_MODEL")
    validation_temperature: float = Field(alias="VALIDATION_TEMPERATURE", default=0.0)

    # Logger Settings
    debug: bool = Field(alias="DEBUG")
    sql_echo: bool = Field(alias="SQL_ECHO")

    model_config = SettingsConfigDict(
        env_file=(f"{ENV_PATH}/.env", f"{ENV_PATH}/.secret"),
        case_sensitive=True,
        env_file_encoding="utf-8",
        frozen=True,
    )


settings = Settings()
