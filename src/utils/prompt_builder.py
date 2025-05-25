import json
from pathlib import Path

import aiofiles
from async_lru import alru_cache
from pydantic import ValidationError

from src import PROMPT_PATH
from src.models.app.validation import ValidationModel


@alru_cache(maxsize=4)  # Cache up to 4 prompts
async def _load_prompt(path: Path) -> dict[str, str]:
    """Internal helper function to load a prompt from a JSON file asynchronously."""
    async with aiofiles.open(path, mode="r") as file:
        content = await file.read()
        return json.loads(content)


async def build_response_fix_prompt(
    content: str, model: type[ValidationModel], error: ValidationError
) -> tuple[str, str]:
    """
    Constructs a prompt pair for fixing an invalid JSON output to a specified JSON schema.

    Args:
        content (str): The invalid JSON output to be fixed.
        model (type[ValidationModel]): The JSON schema to which the output should be fixed.
        error (ValidationError): The validation error from the original attempt
    Returns:
        tuple[str, str]:
        A tuple containing (system prompt, user prompt) pair in that order.
    """
    try:
        prompt_path = PROMPT_PATH / "validation" / "validation.txt"

        system_prompt_data = await _load_prompt(prompt_path / "system.txt")
        system_prompt = system_prompt_data["message"]

        user_prompt_data = await _load_prompt(prompt_path / "user.txt")
        user_prompt = user_prompt_data["message"].format(
            json_output=content, json_schema=model.model_json_schema(), error=error
        )

        return system_prompt, user_prompt

    except Exception as e:
        raise RuntimeError(
            f"Error in build_validation_prompt: {str(e)}. Ensure the prompt files exist, "
            f"contain the required keys ('message'), and the provided content and model are valid for formatting."
        )
