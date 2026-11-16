"""Gemini structured completion boundary. Never expose provider bodies or keys."""
import json
from typing import Protocol, TypeVar
import httpx
from pydantic import BaseModel, ValidationError
from app.core import settings

T = TypeVar('T', bound=BaseModel)

class ModelError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status

class ModelGateway(Protocol):
    async def generate(self, instruction: str, data: dict, schema: type[T], max_tokens: int | None = None) -> T: ...

def configured() -> bool:
    return bool(settings.gemini_api_key.get_secret_value().strip() and settings.llm_model.strip())

class HostedGateway:
    async def generate(self, instruction: str, data: dict, schema: type[T], max_tokens: int | None = None) -> T:
        if not configured():
            raise ModelError('Gemini is not configured. Set GEMINI_API_KEY in backend/.env, then restart.', 503)
        # JSON mode plus schema instructions; Pydantic and evidence validation remain authoritative.
        system = instruction + '\nReturn ONLY a JSON object matching this schema:\n' + json.dumps(schema.model_json_schema())
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{settings.llm_model}:generateContent'
        prompt_data = {key: value for key, value in data.items() if key != "photo_data"}
        parts = [{'text': json.dumps(prompt_data, ensure_ascii=False)}]
        if data.get("photo_data"):
            header, encoded = data["photo_data"].split(",", 1)
            parts.append({'inlineData': {'mimeType': header[5:-7], 'data': encoded}})
        body = {
            'systemInstruction': {'parts': [{'text': system}]},
            'contents': [{'role': 'user', 'parts': parts}],
            'generationConfig': {'responseMimeType': 'application/json',
                                 'maxOutputTokens': max_tokens or settings.llm_max_output_tokens},
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds, follow_redirects=False) as client:
                response = await client.post(url, headers={'x-goog-api-key': settings.gemini_api_key.get_secret_value().strip()}, json=body)
        except httpx.TimeoutException:
            raise ModelError('Gemini timed out. Your writing is saved; retry the reply.', 504) from None
        except httpx.HTTPError:
            raise ModelError('Could not reach Gemini. Your writing is saved; check your connection.', 502) from None
        if response.status_code in {401, 403}:
            raise ModelError('Google rejected the Gemini key or access. Check GEMINI_API_KEY, its project/API restrictions and regional availability in Google AI Studio.', 503)
        if response.status_code == 429:
            raise ModelError('Gemini quota or rate limit reached. Check the limits in Google AI Studio. Wait for the limit to reset, then retry your saved message. No automatic retry or paid fallback was used.', 429)
        if response.status_code == 404:
            raise ModelError('This Gemini model is unavailable for your project. Check LLM_MODEL against the models available in Google AI Studio.', 503)
        if response.status_code in {400, 422}:
            raise ModelError('Gemini rejected the key or request settings. Check GEMINI_API_KEY, LLM_MODEL and free-tier availability for your region in Google AI Studio.', 503)
        if response.status_code >= 400:
            raise ModelError('Gemini is temporarily unavailable. Your writing is saved; retry later.', 502)
        try:
            payload = response.json()
            if payload.get('promptFeedback', {}).get('blockReason'):
                raise ModelError('Gemini blocked this request under its safety policy. No AI response was saved.', 422)
            candidates = payload.get('candidates', [])
            if not candidates:
                raise ValueError('missing candidate')
            candidate = candidates[0]
            if candidate.get('finishReason') in {'SAFETY', 'BLOCKLIST', 'PROHIBITED_CONTENT', 'SPII', 'RECITATION'}:
                raise ModelError('Gemini blocked this response under its safety policy. No AI response was saved.', 422)
            if candidate.get('finishReason') != 'STOP':
                raise ValueError('incomplete response')
            text = ''.join(part.get('text', '') for part in candidate.get('content', {}).get('parts', []) if not part.get('thought', False))
            return schema.model_validate_json(text)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ValidationError):
            raise ModelError('Gemini returned an incomplete or invalid response. Nothing generated was saved; please retry.') from None

def get_gateway() -> ModelGateway:
    return HostedGateway()
