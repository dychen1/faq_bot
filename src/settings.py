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

    # App Settings
    app_name: str = Field(alias="APP_NAME")
    app_port: int = Field(alias="APP_PORT")
    thread_pool_size: int | None = Field(
        alias="APP_THREAD_POOL_SIZE", default=2
    )  # if None, use 2 - 1 for event loop 1 for logger

    # Yelp Settings
    yelp_base_url: str = Field(alias="YELP_BASE_URL")

    # Logger Settings
    debug: bool = Field(alias="DEBUG")

    model_config = SettingsConfigDict(
        env_file=(f"{ENV_PATH}/.env", f"{ENV_PATH}/.secret"),
        case_sensitive=True,
        env_file_encoding="utf-8",
        frozen=True,
    )


settings = Settings()
