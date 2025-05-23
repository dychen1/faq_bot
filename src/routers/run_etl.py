from fastapi import APIRouter, Depends

from src.models.request import RunETLRequest
from src.models.response import RunETLResponse
from src.utils.state import State, get_state
from src.utils.yelp import YelpBusinessSearch, YelpBusinessSearchParams

router = APIRouter()


@router.post("/run_etl")
async def run_etl(request: RunETLRequest, state: State = Depends(get_state)) -> RunETLResponse:
    successful: list[str] = []
    missing: list[str] = []
    search = YelpBusinessSearch(state.yelp_client)
    for business in request.businesses:
        response = await search.query(
            YelpBusinessSearchParams(
                location_name=business.location_name, zip_code=business.zip_code, phone_number=business.phone_number
            ),
        )
        if response:
            successful.append(business.location_name)
        else:
            missing.append(business.location_name)
    # Can supplement with google places data for businesses that are missing from yelp

    return RunETLResponse(
        successful=successful,
        missing=missing,
    )
