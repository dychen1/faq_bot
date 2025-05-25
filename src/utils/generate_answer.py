from typing import TypeVar

from google.genai.types import GenerateContentConfig
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_random_exponential

from src.utils.prompt_builder import build_response_fix_prompt
from src.utils.state import State

ValidationModel = TypeVar("ValidationModel", bound=BaseModel)


@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(min=0.5, max=5))
async def generate_gemini_model_validated_answer(
    state: State, prompt: tuple[str, str], model: type[ValidationModel], repair: bool = True
) -> ValidationModel:
    """
    Makes a Google Gemini generate content API call with retry logic and validates the response against a Pydantic
    model.

    Args:
        state (State): Application state containing Google AI client and settings
        prompt (tuple[str, str]): tuple of system and user prompts to send to the API
        model (type[ValidationModel]): Pydantic model to specify the JSON response structure and validate the response
        against
        repair (bool): Whether to attempt to repair the response if it is not valid

    Returns:
        ValidationModel:
        A Pydantic model instance.
        If the answer is empty, an empty instance of the model is returned.
    """

    system_prompt, user_prompt = prompt
    generated_content = await state.google_client.aio.models.generate_content(
        model=state.settings.chat_model,
        contents=user_prompt,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=state.settings.chat_temperature,
            response_mime_type="application/json",
            response_schema=model,
        ),
    )
    answer_str = generated_content.text if generated_content.text else "I dont know."
    state.logger.debug(f"LLM answer: {answer_str}")

    try:
        validated_answer = model.model_validate_json(answer_str)
        return validated_answer

    except ValidationError as validation_error:
        state.logger.warning(
            "Gemini answering was unable to parse response into model. Attempting validation repair...\n"
        )
        if repair:
            system_fix_prompt, user_fix_prompt = await build_response_fix_prompt(answer_str, model, validation_error)
            return await generate_gemini_model_validated_answer(
                state, (system_fix_prompt, user_fix_prompt), model, repair=False
            )  # Set repair to False to avoid infinite recursion
        else:
            state.logger.error("Error in generate_gemini_model_validated_answer\n", exc_info=True)
            return model.model_construct()

    except Exception:
        state.logger.error("Error in generate_gemini_model_validated_answer\n", exc_info=True)
        return model.model_construct()
