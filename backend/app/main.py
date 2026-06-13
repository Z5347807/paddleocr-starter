from fastapi import FastAPI

from app.models import TemplateInfo
from app.templates import template_infos

app = FastAPI(title="PaddleOCR Web Excel API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/templates", response_model=list[TemplateInfo])
def templates() -> list[TemplateInfo]:
    return template_infos()
