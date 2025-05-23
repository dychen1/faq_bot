import asyncio
import json
import logging

import pandas as pd
from httpx import AsyncClient, Limits

from src.models.app.request import BasicBusinessInfo, GetYelpDataRequest
from src.routers.get_yelp_data import _get_yelp_data_internal
from src.settings import settings


async def main():
    # Set up logging
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

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
    response = await _get_yelp_data_internal(request, yelp_client, logger)

    with open("./data/locations_yelp.json", "w") as f:
        json.dump(response.model_dump(), f, indent=2)

    # Clean up
    await yelp_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
