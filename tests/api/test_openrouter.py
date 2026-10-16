"""OpenRouter extractor over a mocked HTTP transport; no real network (R9, Q6)."""

import base64
import json
import logging
from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr

from test_analysis.extraction import (
    ExtractionFailed,
    ExtractionInvalidResponse,
    ExtractionResult,
    OpenRouterExtractor,
)
from test_analysis.extraction.prompt import SYSTEM_PROMPT

API_KEY = "sk-or-test-secret-0123456789"
MODEL = "vendor/vision-model"
VALID_ANSWER = {
    "items": [
        {
            "test_name_raw": "Hb",
            "value": 131.0,
            "value_raw": "131",
            "unit": "г/л",
            "ref_range": "120-150",
            "flag": None,
            "confidence": 0.9,
            "needs_review": False,
        }
    ]
}

Handler = Callable[[httpx.Request], httpx.Response]


def _completion(content: str | None) -> httpx.Response:
    choices = [
        {
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }
    ]
    return httpx.Response(
        200,
        json={
            "id": "gen-1",
            "object": "chat.completion",
            "created": 0,
            "model": MODEL,
            "choices": choices,
        },
    )


def _extractor(
    handler: Handler, requests: list[httpx.Request] | None = None
) -> OpenRouterExtractor:
    def recording_handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        return handler(request)

    return OpenRouterExtractor(
        api_key=SecretStr(API_KEY),
        model=MODEL,
        timeout_s=5,
        http_client=httpx.Client(transport=httpx.MockTransport(recording_handler)),
    )


def test_extract_valid_answer_returns_result() -> None:
    extractor = _extractor(lambda request: _completion(json.dumps(VALID_ANSWER)))

    result = extractor.extract([b"page"], source=b"original")

    assert result == ExtractionResult.model_validate(VALID_ANSWER)
    assert extractor.model_id == MODEL


def test_extract_request_sends_all_pages_with_strict_schema() -> None:
    requests: list[httpx.Request] = []
    extractor = _extractor(lambda request: _completion(json.dumps(VALID_ANSWER)), requests)
    pages = [b"first page png", b"second page png"]

    extractor.extract(pages, source=b"original pdf")

    (request,) = requests
    body = json.loads(request.content)
    assert request.url == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert body["model"] == MODEL
    assert body["temperature"] == 0
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["response_format"]["json_schema"]["schema"] == (
        ExtractionResult.model_json_schema()
    )
    system, user = body["messages"]
    assert system == {"role": "system", "content": SYSTEM_PROMPT}
    assert [part["image_url"]["url"] for part in user["content"]] == [
        f"data:image/png;base64,{base64.b64encode(page).decode()}" for page in pages
    ]
    assert base64.b64encode(b"original pdf").decode() not in request.content.decode()


def test_extract_invalid_then_valid_answer_retries_once() -> None:
    answers = iter(['{"items": [{"oops": 1}]}', json.dumps(VALID_ANSWER)])
    requests: list[httpx.Request] = []
    extractor = _extractor(lambda request: _completion(next(answers)), requests)

    result = extractor.extract([b"page"], source=b"")

    assert len(result.items) == 1
    assert len(requests) == 2


@pytest.mark.parametrize("content", ["not json", '{"items": "nope"}', None])
def test_extract_two_invalid_answers_raise_invalid_response(content: str | None) -> None:
    requests: list[httpx.Request] = []
    extractor = _extractor(lambda request: _completion(content), requests)

    with pytest.raises(ExtractionInvalidResponse):
        extractor.extract([b"page"], source=b"")

    assert len(requests) == 2


def test_extract_empty_choices_raise_invalid_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        response = _completion("")
        payload = json.loads(response.content)
        payload["choices"] = []
        return httpx.Response(200, json=payload)

    with pytest.raises(ExtractionInvalidResponse):
        _extractor(handler).extract([b"page"], source=b"")


@pytest.mark.parametrize("status_code", [400, 401, 429, 500, 503])
def test_extract_http_error_raises_failed_without_retry(status_code: int) -> None:
    requests: list[httpx.Request] = []
    extractor = _extractor(
        lambda request: httpx.Response(status_code, json={"error": {"message": API_KEY}}),
        requests,
    )

    with pytest.raises(ExtractionFailed, match=str(status_code)) as error:
        extractor.extract([b"page"], source=b"")

    assert API_KEY not in str(error.value)
    assert len(requests) == 1


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (httpx.ReadTimeout("timed out"), "timed out"),
        (httpx.ConnectError("connection refused"), "failed"),
    ],
)
def test_extract_network_error_raises_failed(error: httpx.HTTPError, message: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    with pytest.raises(ExtractionFailed, match=message):
        _extractor(handler).extract([b"page"], source=b"")


def test_extract_logs_never_contain_api_key(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    extractor = _extractor(lambda request: _completion("not json"))

    with pytest.raises(ExtractionInvalidResponse) as error:
        extractor.extract([b"page"], source=b"")

    assert "invalid answer" in caplog.text
    assert API_KEY not in caplog.text
    assert API_KEY not in str(error.value)
