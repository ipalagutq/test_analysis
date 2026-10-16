"""Extractor that sends scan pages to a vision-LLM through the OpenRouter API."""

import base64
import logging

import httpx
import openai
from openai.types.chat import ChatCompletionContentPartParam, ChatCompletionMessageParam
from pydantic import SecretStr, ValidationError

from test_analysis.extraction.base import ExtractionFailed, ExtractionInvalidResponse
from test_analysis.extraction.prompt import SYSTEM_PROMPT
from test_analysis.extraction.schema import ExtractionResult

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ATTEMPTS = 2  # one retry on an answer that fails schema validation

logger = logging.getLogger(__name__)


class OpenRouterExtractor:
    """Reads all scan pages in one chat completion with a strict JSON-schema answer."""

    def __init__(
        self,
        api_key: SecretStr,
        model: str,
        timeout_s: float,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        # SDK retries would stretch one call past LLM_TIMEOUT_S
        self._client = openai.OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key.get_secret_value(),
            timeout=timeout_s,
            max_retries=0,
            http_client=http_client,
        )

    @property
    def model_id(self) -> str:
        """Identifier of the model stored with the draft and the visit."""
        return self._model

    def extract(self, pages: list[bytes], *, source: bytes) -> ExtractionResult:
        """Send PNG pages to the model and validate its answer; `source` is not sent."""
        messages = _build_messages(pages)
        for attempt in range(1, ATTEMPTS + 1):
            content = self._complete(messages)
            try:
                return ExtractionResult.model_validate_json(content or "")
            except ValidationError as error:
                logger.warning(
                    "model %s returned an invalid answer (attempt %d/%d): %d errors",
                    self._model,
                    attempt,
                    ATTEMPTS,
                    error.error_count(),
                )
        raise ExtractionInvalidResponse(
            f"model {self._model} did not return a valid answer after {ATTEMPTS} attempts"
        )

    def _complete(self, messages: list[ChatCompletionMessageParam]) -> str | None:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "extraction_result",
                        "strict": True,
                        "schema": ExtractionResult.model_json_schema(),
                    },
                },
            )
        except openai.APIStatusError as error:
            # the SDK error text may echo the request, so only the status is reported
            raise ExtractionFailed(f"OpenRouter returned HTTP {error.status_code}") from error
        except openai.APITimeoutError as error:
            raise ExtractionFailed("OpenRouter request timed out") from error
        except openai.APIError as error:
            raise ExtractionFailed(f"OpenRouter request failed: {type(error).__name__}") from error
        if not completion.choices:
            return None
        return completion.choices[0].message.content


def _build_messages(pages: list[bytes]) -> list[ChatCompletionMessageParam]:
    images: list[ChatCompletionContentPartParam] = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64.b64encode(page).decode()}"},
        }
        for page in pages
    ]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": images},
    ]
