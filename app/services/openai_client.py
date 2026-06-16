from collections.abc import Sequence
<<<<<<< HEAD
import json
from typing import TypeVar

import httpx
=======
from typing import TypeVar

>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
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


<<<<<<< HEAD
def get_gemini_api_key() -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY is not configured.",
        )
    return settings.gemini_api_key


=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
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

<<<<<<< HEAD

def _extract_gemini_text(response_body: dict[str, object]) -> str:
    candidates = response_body.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("Gemini response did not include candidates.")

    candidate = candidates[0]
    if not isinstance(candidate, dict):
        raise RuntimeError("Gemini response candidate was not an object.")

    content = candidate.get("content")
    if not isinstance(content, dict):
        finish_reason = candidate.get("finishReason")
        raise RuntimeError(f"Gemini response did not include content. finishReason={finish_reason}")

    parts = content.get("parts")
    if not isinstance(parts, list):
        raise RuntimeError("Gemini response did not include content parts.")

    texts = [part.get("text") for part in parts if isinstance(part, dict) and isinstance(part.get("text"), str)]
    if not texts:
        raise RuntimeError("Gemini response did not include text output.")
    return "\n".join(texts)


def parse_with_gemini(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[ParsedModel],
) -> ParsedModel:
    settings = get_settings()
    api_key = get_gemini_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    schema = output_model.model_json_schema()
    gemini_user_prompt = user_prompt
    if not settings.gemini_response_schema_enabled:
        gemini_user_prompt = f"""
{user_prompt}

Return only valid JSON that matches this JSON Schema. Do not wrap the JSON in
Markdown fences and do not include extra commentary:
{json.dumps(schema, ensure_ascii=False)}
"""

    generation_config: dict[str, object] = {
        "temperature": 0.2,
        "responseMimeType": "application/json",
    }
    if settings.gemini_response_schema_enabled:
        generation_config["responseSchema"] = schema

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": gemini_user_prompt}]}],
        "generationConfig": generation_config,
    }

    try:
        response = httpx.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        output_text = _extract_gemini_text(response.json())
        return output_model.model_validate_json(output_text)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:1000]
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini structured output request failed: {detail}",
        ) from exc
    except (httpx.HTTPError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini structured output request failed: {exc}",
        ) from exc


def parse_with_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[ParsedModel],
) -> ParsedModel:
    settings = get_settings()
    if settings.active_llm_provider == "gemini":
        return parse_with_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_model=output_model,
        )
    return parse_with_openai(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=output_model,
    )
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
