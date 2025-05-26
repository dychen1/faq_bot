import asyncio

import httpx
from pydantic import BaseModel

from src.settings import settings


class AnswerRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


async def make_request(client: httpx.AsyncClient, question: str) -> str:
    response = await client.post(
        f"http://localhost:{settings.app_port}/answer",
        json=AnswerRequest(question=question).model_dump(),
        headers={"x-api-key": settings.api_key},
    )
    response.raise_for_status()
    return AnswerResponse(**response.json()).answer


async def main() -> None:
    questions: list[str] = [
        "What are the addresses and phone numbers of each business?",
        "How many businesses are registered zip code 94608?",
        "How many businesses offer WIFI?",
        "Which businesses serve alcohol?",
        "Which businesses offer WIFI and give me their addresses?",
        "Is there parking at Fournée Bakery?",
    ]

    async with httpx.AsyncClient(timeout=120) as client:
        tasks: list[asyncio.Task[str]] = [asyncio.create_task(make_request(client, question)) for question in questions]

        for question, task in zip(questions, tasks):
            print(f"\nQuestion: {question}")
            try:
                answer = await task
                print(f"Answer: {answer}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
