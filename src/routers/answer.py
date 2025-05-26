from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.app.request import AnswerRequest
from src.models.app.response import AnswerResponse
from src.models.app.validation import GeneratedAnswer, GeneratedSQL
from src.models.database.sqlite import Business, Location, Tag
from src.utils.database import get_session
from src.utils.generate_answer import generate_gemini_model_validated_answer
from src.utils.prompt_builder import build_answer_generation_prompt, build_sql_generation_prompt
from src.utils.state import State, get_state
from src.utils.validate_sql import validate_and_limit_sql

router = APIRouter()


@router.post("/answer")
async def answer(
    request: AnswerRequest, state: State = Depends(get_state), session: AsyncSession = Depends(get_session)
) -> AnswerResponse:
    # Generate SQL
    sql_generation_system_prompt, sql_generation_user_prompt = await build_sql_generation_prompt(
        request.question, state.db.dialect, [Business, Location, Tag]
    )
    generated_sql: GeneratedSQL = await generate_gemini_model_validated_answer(
        state, (sql_generation_system_prompt, sql_generation_user_prompt), GeneratedSQL
    )
    state.logger.info(f"Generated SQL for user question '{request.question}': {generated_sql.generated_sql}")

    validation_result = await state.run_in_thread_pool(
        validate_and_limit_sql, generated_sql.generated_sql, state.db.dialect, state.logger
    )
    state.logger.info(f"Validation result: {validation_result}")
    if not validation_result.is_valid:
        return AnswerResponse(answer="I'm sorry, I can't answer that question.")
    assert validation_result.validated_query is not None  # cant be None if valid sql
    sql_query: str = validation_result.validated_query

    # Run SQL in db
    result = await session.execute(text(sql_query))
    rows = result.all()
    state.logger.info(f"DB query result: {rows}")

    # Generate answer
    answer_generation_system_prompt, answer_generation_user_prompt = await build_answer_generation_prompt(
        request.question, sql_query, rows
    )
    answer = await generate_gemini_model_validated_answer(
        state, (answer_generation_system_prompt, answer_generation_user_prompt), GeneratedAnswer
    )
    state.logger.info(f"Generated answer: {answer}")
    return AnswerResponse(answer=answer.answer)
