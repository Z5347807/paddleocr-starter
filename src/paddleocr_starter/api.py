from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile

from .ocr import recognize_image

app = FastAPI(title="PaddleOCR Starter")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)) -> dict[str, object]:
    suffix = Path(file.filename or "upload.png").suffix or ".png"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        return {"filename": file.filename, "results": recognize_image(tmp_path)}
    finally:
        tmp_path.unlink(missing_ok=True)

