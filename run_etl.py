import asyncio
import json
import logging
from pathlib import Path

import pandas as pd
from httpx import AsyncClient, Limits
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.models.app.request import BasicBusinessInfo, GetYelpDataRequest
from src.models.database.tables import Base, Business, Location, Tag
from src.routers.get_yelp_data import _get_yelp_data
from src.settings import settings
from src.utils.logger import get_queue_logger


async def get_yelp_data_and_dump_to_json(logger: logging.Logger):
    # Create state with Yelp client
    yelp_client = AsyncClient(
        limits=Limits(
            max_connections=10,
            max_keepalive_connections=1,
            keepalive_expiry=300,
        ),
        timeout=120,
    )
    yelp_client.headers.update({"Authorization": f"Bearer {settings.yelp_api_key}", "Content-Type": "application/json"})

    # Read and process data
    df = pd.read_csv("./data/locations.csv")
    businesses = [
        BasicBusinessInfo(
            location_name=row["name"] if pd.notna(row["name"]) else None,
            phone_number=row["phone"] if pd.notna(row["phone"]) else None,
            zip_code=str(row["zip_code"]) if pd.notna(row["zip_code"]) else None,
        )
        for row in df.to_dict("records")
    ]
    request = GetYelpDataRequest(businesses=businesses)
    response = await _get_yelp_data(request, yelp_client, logger)

    # Dump data to json file -> Can be treated as an artifact for debugging -> ideally saved to s3 or some bucket
    with open("./data/locations_yelp.json", "w") as f:
        json.dump(response.model_dump(), f, indent=2)

    # Clean up
    await yelp_client.aclose()


def _create_database(logger: logging.Logger, db_url: str = settings.database_url) -> None:
    """
    Create a new SQLite database with all tables defined in the models.

    Args:
        logger: The logger to use.
        db_url: The database URL to connect to. Defaults to the database URL in the settings.
    """
    # Create the engine
    engine = create_engine(db_url, echo=settings.sql_echo)

    # Create all tables
    Base.metadata.create_all(engine)

    # Verify the tables were created
    with Session(engine) as session:
        # This will raise an error if the tables don't exist
        session.execute(text("SELECT 1 FROM businesses"))
        session.execute(text("SELECT 1 FROM locations"))
        session.execute(text("SELECT 1 FROM tags"))
        logger.info("All tables created successfully!")


def load_json_data_to_db(logger: logging.Logger) -> None:
    """
    Load data from locations_yelp.json into the SQLite database.

    Args:
        logger: The logger to use for logging operations.
    """
    db_name: str = settings.database_url.split("/")[-1]
    db_path: Path = Path(f"./data/{db_name}")
    if not db_path.exists():
        logger.info(f"Creating database {db_name} ...")
        _create_database(logger)

    engine = create_engine(settings.database_url, echo=settings.sql_echo)

    with Session(engine) as session:
        with open("./data/locations_yelp.json", "r") as f:
            data = json.load(f)
            for business_data in data["data"]:
                business_info = business_data["business_data"]
                location_info = business_data["location_data"]
                business_tags = business_data["business_tags"]

                logger.info(f"Loading business {business_info['name']} ...")

                # Create business record
                business_model = Business(
                    name=business_info["name"],
                    url=business_info["url"],
                    source=business_info["source"],
                    source_id=business_info["source_id"],
                    source_url=business_info["source_url"],
                    source_rating=business_info["source_rating"],
                    phone=business_info["phone"] if business_info["phone"] else None,
                )

                # Create location record
                location_model = Location(
                    longitude=location_info["longitude"],
                    latitude=location_info["latitude"],
                    address=location_info["address"],
                    city=location_info["city"],
                    zip_code=location_info["zip_code"],
                    country=location_info["country"],
                    state=location_info["state"],
                    active=location_info["active"],
                )
                # Link location to business
                business_model.locations.append(location_model)

                # Link tags to business if tag value is True
                business_model.tags.extend([Tag(tag=tag) for tag, val in business_tags.items() if val is True])

                session.add(business_model)

            # Commit all changes
            session.commit()
            logger.info("Successfully loaded all data into database!")


async def main():
    logger, listener = get_queue_logger(settings.app_name)
    try:
        asyncio.run(get_yelp_data_and_dump_to_json(logger))
        load_json_data_to_db(logger)
    finally:
        listener.stop()


if __name__ == "__main__":
    asyncio.run(main())
