from fastapi import APIRouter, Depends

from src.models.app.request import AnswerRequest
from src.models.app.response import AnswerResponse
from src.utils.state import State, get_state

router = APIRouter()


@router.post("/answer")
async def answer(request: AnswerRequest, state: State = Depends(get_state)) -> AnswerResponse:
    return
