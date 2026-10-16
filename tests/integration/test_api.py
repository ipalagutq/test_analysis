"""HTTP API end to end in fake mode: upload → review → confirm → card (R1, R7, R12–R17, R24)."""

import time
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select

from scan_files import SAMPLES_DIR, make_pdf, make_png
from test_analysis import __version__
from test_analysis.api.uploads import get_request_extractor
from test_analysis.config import get_settings
from test_analysis.extraction import ExtractionFailed, ExtractionInvalidResponse, ExtractionResult
from test_analysis.main import create_app
from test_analysis.patient_card import Result, get_session_factory


@pytest.fixture
def client() -> Iterator[TestClient]:
    """App on a fresh temporary database; the lifespan seeds the demo patients."""
    with TestClient(create_app()) as test_client:
        yield test_client


def _results_count() -> int:
    with get_session_factory()() as session:
        return session.scalar(select(func.count()).select_from(Result)) or 0


def _upload(client: TestClient, data: bytes, patient_id: int = 1, name: str = "scan.png"):
    return client.post(
        "/api/uploads",
        data={"patient_id": str(patient_id)},
        files={"file": (name, data, "application/octet-stream")},
    )


def _upload_sample(client: TestClient, name: str, patient_id: int) -> str:
    response = _upload(client, (SAMPLES_DIR / name).read_bytes(), patient_id, name)
    assert response.status_code == 201, response.text
    return response.json()["draft_id"]


def _confirm_body(rows: list[dict], collected_at: str = "2026-10-01") -> dict:
    return {
        "collected_at": collected_at,
        "rows": [
            {
                "row_id": row["row_id"],
                "code": row["code"],
                "canonical_value": row["canonical_value"],
                "include": row["include"],
            }
            for row in rows
        ],
    }


def _assert_error(response, status_code: int, error: str) -> dict:
    assert response.status_code == status_code, response.text
    body = response.json()
    assert body["error"] == error
    assert isinstance(body["detail"], str)
    return body


def test_health_reports_version_and_fake_mode(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "extractor": "fake"}


def test_startup_on_empty_database_seeds_demo_patients(client: TestClient) -> None:
    response = client.get("/api/patients")

    assert response.status_code == 200
    patients = response.json()
    assert [patient["id"] for patient in patients] == [1, 2, 3]
    assert set(patients[0]) == {"id", "display_name", "sex", "birth_year"}


def test_restart_does_not_seed_again(client: TestClient) -> None:
    with TestClient(create_app()) as restarted:
        assert len(restarted.get("/api/patients").json()) == 3
        assert len(restarted.get("/api/patients/1/timeline").json()) == 3


def test_catalog_lists_all_tests(client: TestClient) -> None:
    catalog = client.get("/api/catalog").json()

    assert 30 <= len(catalog) <= 50
    assert {"code": "HGB", "name_ru": "Гемоглобин", "unit": "г/л", "group": "cbc"} in catalog


def test_samples_list_and_download(client: TestClient) -> None:
    samples = client.get("/api/samples").json()

    assert [sample["name"] for sample in samples] == [
        "cbc_ivanova.pdf", "biochem_petrov.jpg", "mixed_sidorova.png",
    ]  # fmt: skip
    for sample in samples:
        response = client.get(f"/api/samples/{sample['name']}")
        assert response.status_code == 200
        assert response.headers["content-type"] == sample["media_type"]
        assert sample["name"] in response.headers["content-disposition"]
        assert response.content == (SAMPLES_DIR / sample["name"]).read_bytes()


@pytest.mark.parametrize("name", ["unknown.pdf", "lab_catalog.json"])
def test_samples_unknown_name_returns_404(client: TestClient, name: str) -> None:
    _assert_error(client.get(f"/api/samples/{name}"), 404, "not_found")


def test_upload_creates_draft_without_touching_results(client: TestClient) -> None:
    results_before = _results_count()

    draft_id = _upload_sample(client, "mixed_sidorova.png", patient_id=3)

    assert _results_count() == results_before
    draft = client.get(f"/api/drafts/{draft_id}").json()
    assert set(draft) == {
        "id", "patient_id", "status", "model", "extractor", "page_count", "rows", "created_at",
    }  # fmt: skip
    assert (draft["id"], draft["patient_id"], draft["status"]) == (draft_id, 3, "draft")
    assert (draft["extractor"], draft["model"], draft["page_count"]) == ("fake", "fake", 1)
    assert len(draft["rows"]) == 10
    unknown = draft["rows"][6]
    assert (unknown["test_name_raw"], unknown["code"], unknown["needs_review"]) == (
        "ГЛЮ", None, True,
    )  # fmt: skip


def test_upload_pdf_sample_stores_original_and_pages(
    client: TestClient, isolated_env: Path
) -> None:
    draft_id = _upload_sample(client, "cbc_ivanova.pdf", patient_id=1)

    draft_dir = isolated_env / "uploads" / draft_id
    assert (draft_dir / "original.pdf").read_bytes() == (
        SAMPLES_DIR / "cbc_ivanova.pdf"
    ).read_bytes()
    assert client.get(f"/api/drafts/{draft_id}").json()["page_count"] == 2
    for page_number in (0, 1):
        page = client.get(f"/api/drafts/{draft_id}/pages/{page_number}")
        assert page.status_code == 200
        assert page.headers["content-type"] == "image/png"
        assert page.content == (draft_dir / f"page_{page_number}.png").read_bytes()


@pytest.mark.parametrize("page_number", [-1, 2, 99])
def test_draft_page_out_of_range_returns_404(client: TestClient, page_number: int) -> None:
    draft_id = _upload_sample(client, "cbc_ivanova.pdf", patient_id=1)

    _assert_error(client.get(f"/api/drafts/{draft_id}/pages/{page_number}"), 404, "not_found")


def test_upload_converts_units_by_catalog(client: TestClient) -> None:
    draft_id = _upload_sample(client, "biochem_petrov.jpg", patient_id=2)

    rows = client.get(f"/api/drafts/{draft_id}").json()["rows"]
    glucose = rows[0]
    hemoglobin = rows[10]
    assert (glucose["code"], glucose["canonical_unit"]) == ("GLU", "ммоль/л")
    assert glucose["canonical_value"] == pytest.approx(5.772, abs=0.01)
    assert (hemoglobin["code"], hemoglobin["canonical_value"]) == ("HGB", pytest.approx(148))


def test_upload_unknown_patient_returns_404(client: TestClient) -> None:
    _assert_error(_upload(client, make_png(), patient_id=999), 404, "patient_not_found")


def test_upload_text_file_returns_415(client: TestClient) -> None:
    response = _upload(client, b"plain text pretending to be a pdf", name="scan.pdf")

    _assert_error(response, 415, "unsupported_media_type")


def test_upload_file_over_limit_returns_413(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    get_settings.cache_clear()

    response = _upload(client, make_png() + b"\0" * (1024 * 1024))

    _assert_error(response, 413, "file_too_large")


def test_upload_pdf_with_too_many_pages_returns_422(client: TestClient) -> None:
    response = _upload(client, make_pdf(pages=6), name="scan.pdf")

    _assert_error(response, 422, "too_many_pages")


def test_upload_without_file_returns_validation_error(client: TestClient) -> None:
    response = client.post("/api/uploads", data={"patient_id": "1"})

    _assert_error(response, 422, "validation_error")


class _FailingExtractor:
    def __init__(self, error: Exception) -> None:
        self._error = error

    @property
    def model_id(self) -> str:
        return "failing"

    def extract(self, pages: list[bytes], *, source: bytes) -> ExtractionResult:
        raise self._error


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (ExtractionFailed("OpenRouter returned HTTP 500"), "extraction_failed"),
        (ExtractionInvalidResponse("no valid answer"), "extraction_invalid_response"),
    ],
)
def test_upload_extraction_error_returns_502_without_draft(
    client: TestClient, isolated_env: Path, error: Exception, code: str
) -> None:
    client.app.dependency_overrides[get_request_extractor] = lambda: _FailingExtractor(error)

    _assert_error(_upload(client, make_png()), 502, code)

    assert not (isolated_env / "uploads").exists()


def test_unknown_draft_returns_404(client: TestClient) -> None:
    for response in (
        client.get("/api/drafts/missing"),
        client.get("/api/drafts/missing/pages/0"),
        client.post("/api/drafts/missing/confirm", json=_confirm_body([])),
        client.post("/api/drafts/missing/discard"),
    ):
        _assert_error(response, 404, "draft_not_found")


def test_full_scenario_confirmed_rows_reach_timeline_and_trend(client: TestClient) -> None:
    draft_id = _upload_sample(client, "mixed_sidorova.png", patient_id=3)
    rows = client.get(f"/api/drafts/{draft_id}").json()["rows"]
    rows[6]["code"] = "GLU"  # reviewer resolves the unrecognized «ГЛЮ»
    rows[6]["canonical_value"] = 5.2
    rows[4]["include"] = False  # reviewer drops ESR
    trend_before = client.get("/api/patients/3/trends", params={"code": "HGB"}).json()

    response = client.post(f"/api/drafts/{draft_id}/confirm", json=_confirm_body(rows))

    assert response.status_code == 201, response.text
    visit_id = response.json()["visit_id"]
    newest = client.get("/api/patients/3/timeline").json()[0]
    assert (newest["visit_id"], newest["collected_at"], newest["model"]) == (
        visit_id, "2026-10-01", "fake",
    )  # fmt: skip
    codes = [result["code"] for result in newest["results"]]
    assert codes == ["HGB", "WBC", "PLT", "NEUT", "CRP", "GLU", "CREA", "ALT", "TSH"]
    trend_after = client.get("/api/patients/3/trends", params={"code": "HGB"}).json()
    assert len(trend_after["points"]) == len(trend_before["points"]) + 1
    assert trend_after["points"][-1] == {
        "collected_at": "2026-10-01",
        "value": 127.0,
        "flag": "normal",
    }
    assert client.get(f"/api/drafts/{draft_id}").json()["status"] == "confirmed"


def test_confirm_recomputes_flag_ignoring_client(client: TestClient) -> None:
    draft_id = _upload_sample(client, "mixed_sidorova.png", patient_id=3)
    rows = client.get(f"/api/drafts/{draft_id}").json()["rows"]
    hgb = {**rows[0], "canonical_value": 90.0, "flag": "normal"}

    client.post(f"/api/drafts/{draft_id}/confirm", json=_confirm_body([hgb]))

    newest = client.get("/api/patients/3/timeline").json()[0]
    assert newest["results"] == [
        {"code": "HGB", "name_ru": "Гемоглобин", "value": 90.0, "unit": "г/л", "flag": "low"}
    ]


def test_confirm_row_without_code_returns_422_and_writes_nothing(client: TestClient) -> None:
    draft_id = _upload_sample(client, "mixed_sidorova.png", patient_id=3)
    rows = client.get(f"/api/drafts/{draft_id}").json()["rows"]
    results_before = _results_count()
    timeline_before = client.get("/api/patients/3/timeline").json()

    response = client.post(f"/api/drafts/{draft_id}/confirm", json=_confirm_body(rows))

    body = _assert_error(response, 422, "invalid_confirm_rows")
    assert body["row_ids"] == [6]
    assert _results_count() == results_before
    assert client.get("/api/patients/3/timeline").json() == timeline_before
    assert client.get(f"/api/drafts/{draft_id}").json()["status"] == "draft"


def test_confirm_twice_returns_409(client: TestClient) -> None:
    draft_id = _upload_sample(client, "cbc_ivanova.pdf", patient_id=1)
    rows = client.get(f"/api/drafts/{draft_id}").json()["rows"]
    body = _confirm_body(rows)

    assert client.post(f"/api/drafts/{draft_id}/confirm", json=body).status_code == 201
    results_after_first = _results_count()

    _assert_error(
        client.post(f"/api/drafts/{draft_id}/confirm", json=body), 409, "draft_status_conflict"
    )
    _assert_error(client.post(f"/api/drafts/{draft_id}/discard"), 409, "draft_status_conflict")
    assert _results_count() == results_after_first


def test_discard_then_confirm_returns_409(client: TestClient) -> None:
    draft_id = _upload_sample(client, "biochem_petrov.jpg", patient_id=2)
    results_before = _results_count()

    response = client.post(f"/api/drafts/{draft_id}/discard")

    assert response.status_code == 200
    assert response.json()["status"] == "discarded"
    rows = response.json()["rows"]
    _assert_error(
        client.post(f"/api/drafts/{draft_id}/confirm", json=_confirm_body(rows)),
        409,
        "draft_status_conflict",
    )
    _assert_error(client.post(f"/api/drafts/{draft_id}/discard"), 409, "draft_status_conflict")
    assert _results_count() == results_before


def test_confirm_invalid_date_returns_validation_error(client: TestClient) -> None:
    draft_id = _upload_sample(client, "mixed_sidorova.png", patient_id=3)

    response = client.post(
        f"/api/drafts/{draft_id}/confirm", json={"collected_at": "вчера", "rows": []}
    )

    _assert_error(response, 422, "validation_error")


def test_timeline_is_newest_first(client: TestClient) -> None:
    visits = client.get("/api/patients/1/timeline").json()

    dates = [visit["collected_at"] for visit in visits]
    assert dates == sorted(dates, reverse=True)
    result = visits[0]["results"][0]
    assert set(result) == {"code", "name_ru", "value", "unit", "flag"}


def test_trend_is_oldest_first_with_reference(client: TestClient) -> None:
    response = client.get("/api/patients/2/trends", params={"code": "GLU"}).json()

    assert (response["code"], response["unit"]) == ("GLU", "ммоль/л")
    assert (response["ref_low"], response["ref_high"]) == (3.9, 6.1)
    assert response["points"] == [
        {"collected_at": "2026-01-20", "value": 7.2, "flag": "high"},
        {"collected_at": "2026-06-15", "value": 6.0, "flag": "normal"},
    ]


def test_trend_unknown_code_returns_404(client: TestClient) -> None:
    response = client.get("/api/patients/1/trends", params={"code": "NOPE"})

    _assert_error(response, 404, "unknown_test_code")


def test_unknown_patient_card_returns_404(client: TestClient) -> None:
    _assert_error(client.get("/api/patients/999/timeline"), 404, "patient_not_found")
    _assert_error(
        client.get("/api/patients/999/trends", params={"code": "HGB"}), 404, "patient_not_found"
    )


def test_unknown_api_path_returns_json_404(client: TestClient) -> None:
    _assert_error(client.get("/api/does-not-exist"), 404, "not_found")


def test_openrouter_mode_without_credentials_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXTRACTOR", "openrouter")
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="OPENROUTER_API_KEY"):
        create_app()


def test_non_llm_endpoints_respond_within_500_ms(client: TestClient) -> None:
    for path in (
        "/api/health",
        "/api/patients",
        "/api/catalog",
        "/api/patients/1/timeline",
        "/api/patients/1/trends?code=HGB",
    ):
        started = time.perf_counter()
        assert client.get(path).status_code == 200
        assert time.perf_counter() - started <= 0.5, path


def test_fake_upload_of_five_page_pdf_within_3_s(client: TestClient) -> None:
    pdf = make_pdf(pages=5, width=595, height=842)

    started = time.perf_counter()
    response = _upload(client, pdf, name="scan.pdf")

    assert response.status_code == 201
    assert time.perf_counter() - started <= 3
    draft = client.get(f"/api/drafts/{response.json()['draft_id']}").json()
    assert draft["page_count"] == 5
    assert date.fromisoformat(draft["created_at"][:10])
