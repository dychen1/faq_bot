from fastapi import APIRouter, Depends

from src.models.app.request import AnswerRequest
from src.models.app.response import AnswerResponse
from src.utils.generate_answer import generate_gemini_model_validated_answer
from src.utils.state import State, get_state
from src.utils.validate_sql import validate_and_limit_sql

router = APIRouter()


@router.post("/answer")
async def answer(request: AnswerRequest, state: State = Depends(get_state)) -> AnswerResponse:
    generated_sql = "test"
    generate_sql_prompt = prompt
    # Run sync function in thread pool to not block event loop
    validation_result = await state.run_in_thread_pool(
        validate_and_limit_sql, generated_sql, state.db.dialect, state.logger
    )
    answer = await generate_gemini_model_validated_answer(state, request, request.model)
    return
