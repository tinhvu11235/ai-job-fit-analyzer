from collections.abc import Sequence
from typing import TypeVar

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import BaseModel

from app.config import get_settings


ParsedModel = TypeVar("ParsedModel", bound=BaseModel)


class LLMRefusalError(RuntimeError):
    pass


def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured.",
        )
    return OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout_seconds)


def extract_parsed_response(response: object, output_model: type[ParsedModel]) -> ParsedModel:
    output_parsed = getattr(response, "output_parsed", None)
    if output_parsed is not None:
        return output_parsed

    output_items: Sequence[object] = getattr(response, "output", []) or []
    for output in output_items:
        if getattr(output, "type", None) != "message":
            continue
        for content_item in getattr(output, "content", []) or []:
            if getattr(content_item, "type", None) == "refusal":
                refusal = getattr(content_item, "refusal", "The model refused to respond.")
                raise LLMRefusalError(refusal)
            parsed = getattr(content_item, "parsed", None)
            if parsed is not None:
                return parsed

    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_model.model_validate_json(output_text)

    raise RuntimeError("OpenAI response did not include parsed structured output.")


def parse_with_openai(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[ParsedModel],
) -> ParsedModel:
    settings = get_settings()
    client = get_openai_client()

    try:
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=output_model,
        )
        return extract_parsed_response(response, output_model)
    except LLMRefusalError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI structured output request failed: {exc}",
        ) from exc

