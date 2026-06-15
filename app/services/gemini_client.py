from collections.abc import Mapping
from copy import deepcopy
from typing import TypeVar

from fastapi import HTTPException, status
from google import genai
from pydantic import BaseModel

from app.config import get_settings


ParsedModel = TypeVar("ParsedModel", bound=BaseModel)


def get_gemini_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "title": "Thiếu Gemini API key",
                "message": "Backend chưa cấu hình GEMINI_API_KEY.",
                "actions": ["Tạo API key trong Google AI Studio rồi cập nhật biến môi trường GEMINI_API_KEY."],
                "code": "missing_gemini_key",
            },
        )
    return genai.Client(api_key=settings.gemini_api_key)


def _clean_schema_node(node: object, defs: Mapping[str, object]) -> object:
    if isinstance(node, list):
        return [_clean_schema_node(item, defs) for item in node]

    if not isinstance(node, dict):
        return node

    if "$ref" in node:
        ref = node["$ref"]
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[-1]
            resolved = deepcopy(defs.get(name, {}))
            for key, value in node.items():
                if key != "$ref":
                    resolved[key] = value
            return _clean_schema_node(resolved, defs)

    if "anyOf" in node:
        options = [_clean_schema_node(option, defs) for option in node["anyOf"]]
        non_null_options = [option for option in options if not (isinstance(option, dict) and option.get("type") == "null")]
        has_null = len(non_null_options) != len(options)
        if has_null and len(non_null_options) == 1 and isinstance(non_null_options[0], dict):
            nullable_schema = dict(non_null_options[0])
            schema_type = nullable_schema.get("type")
            if isinstance(schema_type, list):
                nullable_schema["type"] = [*schema_type, "null"]
            elif schema_type:
                nullable_schema["type"] = [schema_type, "null"]
            for key, value in node.items():
                if key not in {"anyOf", "default", "title"}:
                    nullable_schema[key] = _clean_schema_node(value, defs)
            return nullable_schema

    cleaned: dict[str, object] = {}
    for key, value in node.items():
        if key in {"$defs", "default", "title"}:
            continue
        cleaned[key] = _clean_schema_node(value, defs)
    return cleaned


def _gemini_schema(output_model: type[ParsedModel]) -> dict[str, object]:
    schema = output_model.model_json_schema()
    defs = schema.get("$defs", {})
    cleaned = _clean_schema_node(schema, defs)
    if not isinstance(cleaned, dict):
        raise RuntimeError("Generated Gemini schema is not an object.")
    return cleaned


def _extract_error_fields(exc: Exception) -> tuple[int | None, str | None, str]:
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    reason = getattr(exc, "reason", None)
    message = str(exc)

    response = getattr(exc, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", status_code)

    return status_code if isinstance(status_code, int) else None, str(reason) if reason else None, message


def _raise_gemini_http_error(exc: Exception) -> None:
    status_code, reason, message = _extract_error_fields(exc)
    normalized = f"{reason or ''} {message}".lower()

    if status_code == 429 or "quota" in normalized or "resource_exhausted" in normalized:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "title": "Gemini đang hết quota hoặc bị giới hạn tốc độ",
                "message": "API key Gemini hiện tại đã chạm giới hạn free tier/rate limit hoặc chưa bật billing cho mức dùng cao hơn.",
                "actions": [
                    "Kiểm tra quota/rate limit của Gemini API trong Google AI Studio hoặc Google Cloud.",
                    "Giảm PUBLIC_DEMO_DAILY_LIMIT nếu đang mở demo công khai.",
                    "Chờ quota free tier reset hoặc nâng cấp billing nếu cần dùng nhiều hơn.",
                ],
                "code": "gemini_quota_or_rate_limit",
            },
        ) from exc

    if status_code in {401, 403} or "api key" in normalized or "permission" in normalized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "title": "Gemini API key không hợp lệ",
                "message": "Backend không thể xác thực với Gemini. Hãy kiểm tra GEMINI_API_KEY và quyền truy cập API.",
                "actions": ["Tạo API key mới trong Google AI Studio rồi cập nhật biến môi trường trên Render."],
                "code": "invalid_gemini_key",
            },
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "title": "Gemini chưa phản hồi thành công",
            "message": "Yêu cầu structured output tới Gemini thất bại. Hãy thử lại hoặc kiểm tra cấu hình model.",
            "actions": [],
            "code": "gemini_request_failed",
        },
    ) from exc


def parse_with_gemini(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[ParsedModel],
) -> ParsedModel:
    settings = get_settings()
    client = get_gemini_client()
    prompt = f"{system_prompt.strip()}\n\nUser request:\n{user_prompt.strip()}"

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "response_format": {
                    "text": {
                        "mime_type": "application/json",
                        "schema": _gemini_schema(output_model),
                    }
                }
            },
        )
        if not response.text:
            raise RuntimeError("Gemini response did not include text.")
        return output_model.model_validate_json(response.text)
    except HTTPException:
        raise
    except Exception as exc:
        _raise_gemini_http_error(exc)
