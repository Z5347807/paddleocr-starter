from io import BytesIO

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

from app.errors import ApiError, api_error_handler
from app.exporter import build_workbook
from app.form_exporter import build_form_workbook
from app.models import RecognitionResult, TemplateInfo
from app.ocr import OcrEngine, get_ocr_engine
from app.templates import DEFAULT_TEMPLATE_ID, get_template, template_infos

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="PaddleOCR Web Excel API")
app.add_exception_handler(ApiError, api_error_handler)


def get_engine() -> OcrEngine:
    return get_ocr_engine()


def resolve_engine() -> OcrEngine:
    override = app.dependency_overrides.get(get_engine)
    if override is not None:
        return override()
    return get_engine()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/templates", response_model=list[TemplateInfo])
def templates() -> list[TemplateInfo]:
    return template_infos()


def _ensure_supported_image(file: UploadFile) -> None:
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise ApiError(
            400,
            "unsupported_file_type",
            "Only JPEG, PNG, and WebP images are supported.",
            file.content_type or "",
        )


def _image_size(image_bytes: bytes) -> tuple[int, int]:
    try:
        image = Image.open(BytesIO(image_bytes))
        return image.size
    except UnidentifiedImageError as exc:
        raise ApiError(400, "image_decode_failed", "Image cannot be decoded.", str(exc)) from exc


def _recognize_result(image_bytes: bytes, filename: str, template_id: str, width: int, height: int) -> RecognitionResult:
    try:
        template = get_template(template_id)
    except KeyError as exc:
        raise ApiError(400, "unknown_template", "Template is not supported.", template_id) from exc

    try:
        engine = resolve_engine()
        raw_lines = engine.recognize(image_bytes)
    except Exception as exc:
        raise ApiError(500, "ocr_failed", "OCR recognition failed.", str(exc)) from exc

    return template.extract(
        raw_lines=raw_lines,
        filename=filename,
        width=width,
        height=height,
    )


@app.post("/api/recognize", response_model=RecognitionResult)
async def recognize(
    file: UploadFile = File(...),
    templateId: str = Form(DEFAULT_TEMPLATE_ID),
) -> RecognitionResult:
    _ensure_supported_image(file)

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise ApiError(400, "file_too_large", "Image file must be 10MB or smaller.", str(len(image_bytes)))

    width, height = _image_size(image_bytes)

    return _recognize_result(
        image_bytes=image_bytes,
        filename=file.filename or "uploaded-image",
        template_id=templateId,
        width=width,
        height=height,
    )


@app.post("/api/export")
def export_excel(result: RecognitionResult) -> Response:
    try:
        content = build_workbook(result)
    except Exception as exc:
        raise ApiError(500, "export_failed", "Excel generation failed.", str(exc)) from exc

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="recognition-result.xlsx"'},
    )


@app.post("/api/export-form")
async def export_form_excel(
    file: UploadFile = File(...),
    templateId: str = Form(DEFAULT_TEMPLATE_ID),
) -> Response:
    _ensure_supported_image(file)

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise ApiError(400, "file_too_large", "Image file must be 10MB or smaller.", str(len(image_bytes)))

    width, height = _image_size(image_bytes)

    result = _recognize_result(
        image_bytes=image_bytes,
        filename=file.filename or "uploaded-image",
        template_id=templateId,
        width=width,
        height=height,
    )

    try:
        content = build_form_workbook(result)
    except Exception as exc:
        raise ApiError(500, "export_failed", "Excel generation failed.", str(exc)) from exc

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="transformer-test-record.xlsx"'},
    )
