from fastapi import APIRouter, Depends

from src.models.app.request import GetYelpDataRequest
from src.models.app.response import GetYelpDataResponse
from src.utils.state import State, get_state
from src.utils.yelp import YelpBusinessData, YelpBusinessSearch, YelpBusinessSearchParams

router = APIRouter()


@router.post("/get_yelp_data")
async def get_yelp_data(request: GetYelpDataRequest, state: State = Depends(get_state)) -> GetYelpDataResponse:
    search = YelpBusinessSearch(state.yelp_client)
    missing: list[str] = []
    data: list[YelpBusinessData] = []
    for business in request.businesses:
        response = await search.query(
            YelpBusinessSearchParams(
                location_name=business.location_name, zip_code=business.zip_code, phone_number=business.phone_number
            ),
        )
        if response:
            data.append(response)
        else:
            missing.append(business.location_name)
            # Can supplement with google places data for businesses that are missing from yelp

    return GetYelpDataResponse(
        data=data,
        missing=missing,
    )
