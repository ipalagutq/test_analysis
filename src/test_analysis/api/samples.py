"""Demo scan routes for the "download example" buttons on the upload screen."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

SAMPLES_DIR = Path("data/samples")


class SampleInfo(BaseModel):
    name: str
    title: str
    media_type: str
    patient_id: int


# fixed list: the requested name is looked up here and never joined into a path as is
SAMPLES = (
    SampleInfo(
        name="cbc_ivanova.pdf",
        title="Общий анализ крови (PDF, 2 стр.)",
        media_type="application/pdf",
        patient_id=1,
    ),
    SampleInfo(
        name="biochem_petrov.jpg",
        title="Биохимия, глюкоза в мг/дл (JPG)",
        media_type="image/jpeg",
        patient_id=2,
    ),
    SampleInfo(
        name="mixed_sidorova.png",
        title="Смешанный бланк (PNG)",
        media_type="image/png",
        patient_id=3,
    ),
)
_SAMPLE_BY_NAME = {sample.name: sample for sample in SAMPLES}

router = APIRouter()


@router.get("/samples")
def list_samples() -> list[SampleInfo]:
    """List demo scans available for download."""
    return list(SAMPLES)


@router.get(
    "/samples/{name}",
    response_class=Response,
    responses={
        200: {"content": {sample.media_type: {} for sample in SAMPLES}},
    },
)
def read_sample(name: str) -> Response:
    """Return a demo scan file as an attachment."""
    sample = _SAMPLE_BY_NAME.get(name)
    if sample is None or not (SAMPLES_DIR / sample.name).is_file():
        raise HTTPException(status_code=404, detail=f"sample {name} not found")
    path = SAMPLES_DIR / sample.name
    return Response(
        content=path.read_bytes(),
        media_type=sample.media_type,
        headers={"Content-Disposition": f'attachment; filename="{sample.name}"'},
    )
