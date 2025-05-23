from logging import Logger

from fastapi import APIRouter, Depends
from httpx import AsyncClient

from src.models.app.request import GetYelpDataRequest
from src.models.app.response import GetYelpDataResponse
from src.utils.state import State, get_state
from src.utils.yelp import YelpBusinessData, YelpBusinessSearch, YelpBusinessSearchParams

router = APIRouter()


@router.post("/get_yelp_data")
async def get_yelp_data(request: GetYelpDataRequest, state: State = Depends(get_state)) -> GetYelpDataResponse:
    return await _get_yelp_data_internal(request, state.yelp_client, state.logger)


async def _get_yelp_data_internal(
    request: GetYelpDataRequest, yelp_client: AsyncClient, logger: Logger
) -> GetYelpDataResponse:
    search = YelpBusinessSearch(yelp_client)
    missing: list[str] = []
    data: list[YelpBusinessData] = []
    for business in request.businesses:
        response = await search.query(
            YelpBusinessSearchParams(
                location_name=business.location_name,
                zip_code=business.zip_code,
                phone_number=business.phone_number,
            ),
        )
        if response:
            logger.info(f"Successfully fetched data for {business.location_name}")
            data.append(response)
        else:
            logger.info(f"No data found for {business.location_name}")
            missing.append(business.location_name)
            # Can supplement with google places data for businesses that are missing from yelp

    logger.info(f"Missing data for {len(missing)} businesses out of {len(request.businesses)}")
    logger.info(f"Missing data for {missing}")
    return GetYelpDataResponse(
        data=data,
        missing=missing,
    )
