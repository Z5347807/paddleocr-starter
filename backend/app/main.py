from fastapi import FastAPI
from fastapi.responses import Response

from app.errors import ApiError, api_error_handler
from app.exporter import build_workbook
from app.models import RecognitionResult, TemplateInfo
from app.templates import template_infos

app = FastAPI(title="PaddleOCR Web Excel API")
app.add_exception_handler(ApiError, api_error_handler)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/templates", response_model=list[TemplateInfo])
def templates() -> list[TemplateInfo]:
    return template_infos()


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
