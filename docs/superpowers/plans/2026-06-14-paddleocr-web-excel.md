# PaddleOCR Web Excel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web app that uploads a photographed transformer test record, recognizes it with PaddleOCR, lets the user edit the extracted result, and exports a corresponding Excel workbook.

**Architecture:** The project is split into a FastAPI backend and a React/Vite frontend. The backend owns file validation, OCR execution, fixed-template extraction, structured API responses, and Excel generation. The frontend owns image upload, preview, editable recognition results, raw OCR inspection, and export download.

**Tech Stack:** Python, FastAPI, Pydantic, PaddleOCR, OpenCV, Pillow, openpyxl, pytest, React, Vite, TypeScript, Vitest, React Testing Library.

---

## File Structure

Create this project structure:

```text
backend/
  pyproject.toml
  app/
    __init__.py
    errors.py
    exporter.py
    main.py
    models.py
    ocr.py
    templates/
      __init__.py
      transformer_short_circuit.py
  tests/
    test_api_export.py
    test_api_health.py
    test_api_recognize.py
    test_exporter.py
    test_templates.py
frontend/
  index.html
  package.json
  tsconfig.json
  tsconfig.node.json
  vite.config.ts
  src/
    App.test.tsx
    App.tsx
    api.ts
    main.tsx
    setupTests.ts
    styles.css
    types.ts
.gitignore
README.md
```

Responsibility boundaries:

- `backend/app/models.py`: shared request and response models.
- `backend/app/errors.py`: API error envelope and exception handler.
- `backend/app/ocr.py`: OCR engine protocol plus PaddleOCR-backed implementation.
- `backend/app/templates/transformer_short_circuit.py`: fixed template definition and extraction rules.
- `backend/app/exporter.py`: Excel workbook generation from edited recognition JSON.
- `backend/app/main.py`: FastAPI routes and dependency wiring.
- `frontend/src/types.ts`: API types mirrored from backend response shape.
- `frontend/src/api.ts`: typed HTTP client helpers.
- `frontend/src/App.tsx`: upload, preview, edit, raw OCR, and export workflow.

## Task 1: Backend Skeleton And Health Endpoint

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api_health.py`

- [ ] **Step 1: Write the failing health endpoint test**

Create `backend/tests/test_api_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
cd backend
pytest tests/test_api_health.py -v
```

Expected: FAIL because `app.main` does not exist yet.

- [ ] **Step 3: Create backend package files**

Create `backend/pyproject.toml`:

```toml
[project]
name = "paddleocr-web-excel-backend"
version = "0.1.0"
description = "Local PaddleOCR web backend for recognizing transformer test record photos and exporting Excel workbooks."
requires-python = ">=3.10"
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "python-multipart",
  "pydantic",
  "pillow",
  "openpyxl",
  "opencv-python-headless",
  "paddleocr"
]

[project.optional-dependencies]
dev = [
  "pytest",
  "httpx"
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Create `backend/app/__init__.py`:

```python
"""PaddleOCR web Excel backend package."""
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="PaddleOCR Web Excel API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run the health test and verify it passes**

Run:

```bash
cd backend
pytest tests/test_api_health.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit backend skeleton**

Run:

```bash
git add backend/pyproject.toml backend/app/__init__.py backend/app/main.py backend/tests/test_api_health.py
git commit -m "feat: add backend health endpoint"
```

## Task 2: Backend Models And Fixed Template Extraction

**Files:**
- Create: `backend/app/models.py`
- Create: `backend/app/templates/__init__.py`
- Create: `backend/app/templates/transformer_short_circuit.py`
- Create: `backend/tests/test_templates.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing template tests**

Create `backend/tests/test_templates.py`:

```python
from app.models import RawOcrLine
from app.templates import DEFAULT_TEMPLATE_ID, get_template, list_templates


def line(text: str, top: float, confidence: float = 0.95) -> RawOcrLine:
    return RawOcrLine(
        text=text,
        confidence=confidence,
        box=[[10.0, top], [400.0, top], [400.0, top + 20.0], [10.0, top + 20.0]],
    )


def test_list_templates_returns_transformer_template() -> None:
    templates = list_templates()

    assert templates == [
        {
            "id": "transformer_short_circuit_test_record",
            "name": "变压器短路承受能力试验现场记录",
        }
    ]
    assert DEFAULT_TEMPLATE_ID == "transformer_short_circuit_test_record"


def test_transformer_template_extracts_fields_and_tables() -> None:
    template = get_template(DEFAULT_TEMPLATE_ID)
    raw_lines = [
        line("变压器短路承受能力试验现场记录", 10),
        line("中心编号：B260112", 30),
        line("委托单位 山东鲁能泰山电力设备有限公司", 50),
        line("型号 SSZ22-63000/110", 70),
        line("序号 LTD-260-0032", 90),
        line("联结组 YNyn0d11", 110),
        line("试验前 1 281.25 281.15 279.05 285.348", 150),
        line("试验前 9B 227.25 227.25 226.85 230.322", 170),
        line("试验过程中 1 281.45 281.45 279.45 1", 210),
        line("试验后 9B 227.45 227.45 226.25", 260),
        line("2026 年 1 月 25 日", 320),
    ]

    result = template.extract(
        raw_lines=raw_lines,
        filename="sample.jpg",
        width=1080,
        height=1920,
    )

    assert result.documentType == DEFAULT_TEMPLATE_ID
    assert result.fields["centerNumber"].value == "B260112"
    assert result.fields["client"].value == "山东鲁能泰山电力设备有限公司"
    assert result.fields["model"].value == "SSZ22-63000/110"
    assert result.fields["serialNumber"].value == "LTD-260-0032"
    assert result.fields["connectionGroup"].value == "YNyn0d11"
    assert result.fields["date"].value == "2026 年 1 月 25 日"
    assert result.tables[0].id == "before_test_reactance"
    assert result.tables[0].rows[0]["分接"] == "1"
    assert result.tables[0].rows[0]["AB"] == "281.25"
    assert result.tables[1].id == "during_test_reactance"
    assert result.tables[2].id == "after_test_reactance"
    assert result.rawOcr == raw_lines
```

- [ ] **Step 2: Run template tests and verify they fail**

Run:

```bash
cd backend
pytest tests/test_templates.py -v
```

Expected: FAIL because `app.models` and `app.templates` do not exist yet.

- [ ] **Step 3: Create shared backend models**

Create `backend/app/models.py`:

```python
from pydantic import BaseModel, Field


class ImageInfo(BaseModel):
    filename: str
    width: int
    height: int


class FieldValue(BaseModel):
    label: str
    value: str
    confidence: float = 0.0
    edited: bool = False


class TableData(BaseModel):
    id: str
    title: str
    columns: list[str]
    rows: list[dict[str, str]]


class RawOcrLine(BaseModel):
    text: str
    confidence: float
    box: list[list[float]]


class WarningItem(BaseModel):
    code: str
    message: str


class RecognitionResult(BaseModel):
    documentType: str
    image: ImageInfo
    fields: dict[str, FieldValue]
    tables: list[TableData]
    rawOcr: list[RawOcrLine]
    warnings: list[WarningItem] = Field(default_factory=list)


class TemplateInfo(BaseModel):
    id: str
    name: str
```

- [ ] **Step 4: Create fixed transformer template extraction**

Create `backend/app/templates/transformer_short_circuit.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import FieldValue, ImageInfo, RawOcrLine, RecognitionResult, TableData, TemplateInfo, WarningItem

TEMPLATE_ID = "transformer_short_circuit_test_record"
TEMPLATE_NAME = "变压器短路承受能力试验现场记录"


def _confidence(lines: list[RawOcrLine]) -> float:
    if not lines:
        return 0.0
    return round(sum(line.confidence for line in lines) / len(lines), 4)


def _find_after_label(lines: list[RawOcrLine], label: str) -> FieldValue:
    for line in lines:
        if label in line.text:
            value = line.text.replace(label, "", 1)
            value = value.replace("：", " ").replace(":", " ").strip()
            return FieldValue(label=label, value=value, confidence=line.confidence)
    return FieldValue(label=label, value="", confidence=0.0)


def _find_date(lines: list[RawOcrLine]) -> FieldValue:
    pattern = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
    for line in lines:
        match = pattern.search(line.text)
        if match:
            return FieldValue(label="日期", value=match.group(1), confidence=line.confidence)
    return FieldValue(label="日期", value="", confidence=0.0)


def _extract_table_rows(lines: list[RawOcrLine], marker: str, columns: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    numeric_pattern = re.compile(
        rf"{re.escape(marker)}\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?"
    )
    for line in lines:
        match = numeric_pattern.search(line.text)
        if not match:
            continue
        values = list(match.groups(default=""))
        row = {columns[index]: values[index] for index in range(min(len(columns), len(values)))}
        rows.append(row)
    return rows


@dataclass(frozen=True)
class TransformerShortCircuitTemplate:
    id: str = TEMPLATE_ID
    name: str = TEMPLATE_NAME

    def info(self) -> TemplateInfo:
        return TemplateInfo(id=self.id, name=self.name)

    def extract(
        self,
        raw_lines: list[RawOcrLine],
        filename: str,
        width: int,
        height: int,
    ) -> RecognitionResult:
        before_columns = ["分接", "AB", "BC", "CA", "电抗(mH)"]
        during_columns = ["分接", "AB", "BC", "CA", "试验次数"]
        after_columns = ["分接", "AB", "BC", "CA"]

        fields = {
            "centerNumber": _find_after_label(raw_lines, "中心编号"),
            "client": _find_after_label(raw_lines, "委托单位"),
            "model": _find_after_label(raw_lines, "型号"),
            "serialNumber": _find_after_label(raw_lines, "序号"),
            "connectionGroup": _find_after_label(raw_lines, "联结组"),
            "date": _find_date(raw_lines),
        }

        tables = [
            TableData(
                id="before_test_reactance",
                title="试验前电抗测量",
                columns=before_columns,
                rows=_extract_table_rows(raw_lines, "试验前", before_columns),
            ),
            TableData(
                id="during_test_reactance",
                title="试验过程中电抗测量",
                columns=during_columns,
                rows=_extract_table_rows(raw_lines, "试验过程中", during_columns),
            ),
            TableData(
                id="after_test_reactance",
                title="试验后电抗测量",
                columns=after_columns,
                rows=_extract_table_rows(raw_lines, "试验后", after_columns),
            ),
        ]

        warnings: list[WarningItem] = []
        if any(value.confidence < 0.7 for value in fields.values()) or _confidence(raw_lines) < 0.8:
            warnings.append(
                WarningItem(
                    code="low_confidence",
                    message="部分识别结果置信度较低，请人工确认后再导出。",
                )
            )

        return RecognitionResult(
            documentType=self.id,
            image=ImageInfo(filename=filename, width=width, height=height),
            fields=fields,
            tables=tables,
            rawOcr=raw_lines,
            warnings=warnings,
        )
```

Create `backend/app/templates/__init__.py`:

```python
from app.models import TemplateInfo
from app.templates.transformer_short_circuit import TEMPLATE_ID, TransformerShortCircuitTemplate

DEFAULT_TEMPLATE_ID = TEMPLATE_ID

_TEMPLATES = {
    TEMPLATE_ID: TransformerShortCircuitTemplate(),
}


def list_templates() -> list[dict[str, str]]:
    return [template.info().model_dump() for template in _TEMPLATES.values()]


def get_template(template_id: str = DEFAULT_TEMPLATE_ID) -> TransformerShortCircuitTemplate:
    return _TEMPLATES[template_id]


def template_infos() -> list[TemplateInfo]:
    return [template.info() for template in _TEMPLATES.values()]
```

- [ ] **Step 5: Add the templates endpoint**

Replace `backend/app/main.py` with:

```python
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
```

- [ ] **Step 6: Run backend tests and verify they pass**

Run:

```bash
cd backend
pytest -v
```

Expected: PASS with `test_api_health.py` and `test_templates.py` passing.

- [ ] **Step 7: Commit models and template extraction**

Run:

```bash
git add backend/app/main.py backend/app/models.py backend/app/templates backend/tests/test_templates.py
git commit -m "feat: add fixed transformer template extraction"
```

## Task 3: Excel Exporter And Export API

**Files:**
- Create: `backend/app/exporter.py`
- Create: `backend/app/errors.py`
- Create: `backend/tests/test_exporter.py`
- Create: `backend/tests/test_api_export.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing exporter tests**

Create `backend/tests/test_exporter.py`:

```python
from io import BytesIO

from openpyxl import load_workbook

from app.exporter import build_workbook
from app.models import FieldValue, ImageInfo, RawOcrLine, RecognitionResult, TableData


def sample_result() -> RecognitionResult:
    return RecognitionResult(
        documentType="transformer_short_circuit_test_record",
        image=ImageInfo(filename="sample.jpg", width=1080, height=1920),
        fields={
            "centerNumber": FieldValue(label="中心编号", value="B260112", confidence=0.93, edited=True),
            "client": FieldValue(label="委托单位", value="山东鲁能泰山电力设备有限公司", confidence=0.91),
        },
        tables=[
            TableData(
                id="before_test_reactance",
                title="试验前电抗测量",
                columns=["分接", "AB", "BC", "CA", "电抗(mH)"],
                rows=[{"分接": "1", "AB": "281.25", "BC": "281.15", "CA": "279.05", "电抗(mH)": "285.348"}],
            )
        ],
        rawOcr=[
            RawOcrLine(
                text="中心编号：B260112",
                confidence=0.93,
                box=[[1.0, 2.0], [3.0, 2.0], [3.0, 4.0], [1.0, 4.0]],
            )
        ],
    )


def test_build_workbook_creates_expected_sheets_and_values() -> None:
    content = build_workbook(sample_result())
    workbook = load_workbook(BytesIO(content))

    assert workbook.sheetnames == ["识别结果", "关键字段", "原始OCR"]
    assert workbook["识别结果"]["A1"].value == "变压器短路承受能力试验现场记录"
    assert workbook["识别结果"]["A3"].value == "中心编号"
    assert workbook["识别结果"]["B3"].value == "B260112"
    assert workbook["识别结果"]["A7"].value == "试验前电抗测量"
    assert workbook["识别结果"]["A9"].value == "1"
    assert workbook["关键字段"]["A2"].value == "centerNumber"
    assert workbook["关键字段"]["E2"].value is True
    assert workbook["原始OCR"]["A2"].value == "中心编号：B260112"
```

- [ ] **Step 2: Write failing export API tests**

Create `backend/tests/test_api_export.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_export_returns_xlsx_file() -> None:
    client = TestClient(app)
    payload = {
        "documentType": "transformer_short_circuit_test_record",
        "image": {"filename": "sample.jpg", "width": 1080, "height": 1920},
        "fields": {
            "centerNumber": {"label": "中心编号", "value": "B260112", "confidence": 0.93, "edited": True}
        },
        "tables": [
            {
                "id": "before_test_reactance",
                "title": "试验前电抗测量",
                "columns": ["分接", "AB", "BC", "CA", "电抗(mH)"],
                "rows": [{"分接": "1", "AB": "281.25", "BC": "281.15", "CA": "279.05", "电抗(mH)": "285.348"}],
            }
        ],
        "rawOcr": [
            {
                "text": "中心编号：B260112",
                "confidence": 0.93,
                "box": [[1.0, 2.0], [3.0, 2.0], [3.0, 4.0], [1.0, 4.0]],
            }
        ],
        "warnings": [],
    }

    response = client.post("/api/export", json=payload)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.headers["content-disposition"] == 'attachment; filename="recognition-result.xlsx"'
    assert response.content.startswith(b"PK")
```

- [ ] **Step 3: Run export tests and verify they fail**

Run:

```bash
cd backend
pytest tests/test_exporter.py tests/test_api_export.py -v
```

Expected: FAIL because `app.exporter` and `/api/export` do not exist yet.

- [ ] **Step 4: Create API error envelope**

Create `backend/app/errors.py`:

```python
from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, detail: str = "") -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "detail": exc.detail,
            }
        },
    )
```

- [ ] **Step 5: Create Excel exporter**

Create `backend/app/exporter.py`:

```python
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.models import RecognitionResult

TITLE = "变压器短路承受能力试验现场记录"


def _style_header(row) -> None:
    fill = PatternFill(fill_type="solid", fgColor="E8EEF7")
    for cell in row:
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _autosize(sheet) -> None:
    for column in sheet.columns:
        width = 12
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            value = "" if cell.value is None else str(cell.value)
            width = max(width, min(len(value) + 4, 42))
        sheet.column_dimensions[column_letter].width = width


def _write_result_sheet(workbook: Workbook, result: RecognitionResult) -> None:
    sheet = workbook.active
    sheet.title = "识别结果"
    sheet["A1"] = TITLE
    sheet["A1"].font = Font(bold=True, size=16)
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)

    row_index = 3
    for field in result.fields.values():
        sheet.cell(row=row_index, column=1, value=field.label)
        sheet.cell(row=row_index, column=2, value=field.value)
        row_index += 1

    row_index += 1
    for table in result.tables:
        sheet.cell(row=row_index, column=1, value=table.title)
        sheet.cell(row=row_index, column=1).font = Font(bold=True)
        row_index += 1
        for column_index, column_name in enumerate(table.columns, start=1):
            sheet.cell(row=row_index, column=column_index, value=column_name)
        _style_header(sheet[row_index])
        row_index += 1
        for row in table.rows:
            for column_index, column_name in enumerate(table.columns, start=1):
                sheet.cell(row=row_index, column=column_index, value=row.get(column_name, ""))
            row_index += 1
        row_index += 1

    _autosize(sheet)


def _write_fields_sheet(workbook: Workbook, result: RecognitionResult) -> None:
    sheet = workbook.create_sheet("关键字段")
    headers = ["Field id", "Field label", "Value", "Confidence", "User edited flag"]
    sheet.append(headers)
    _style_header(sheet[1])
    for field_id, field in result.fields.items():
        sheet.append([field_id, field.label, field.value, field.confidence, field.edited])
    _autosize(sheet)


def _write_raw_ocr_sheet(workbook: Workbook, result: RecognitionResult) -> None:
    sheet = workbook.create_sheet("原始OCR")
    headers = ["Text", "Confidence", "Box coordinates"]
    sheet.append(headers)
    _style_header(sheet[1])
    for line in result.rawOcr:
        sheet.append([line.text, line.confidence, str(line.box)])
    _autosize(sheet)


def build_workbook(result: RecognitionResult) -> bytes:
    workbook = Workbook()
    _write_result_sheet(workbook, result)
    _write_fields_sheet(workbook, result)
    _write_raw_ocr_sheet(workbook, result)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
```

- [ ] **Step 6: Add export route**

Replace `backend/app/main.py` with:

```python
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
```

- [ ] **Step 7: Run backend tests and verify they pass**

Run:

```bash
cd backend
pytest -v
```

Expected: PASS with health, template, exporter, and export API tests passing.

- [ ] **Step 8: Commit Excel export**

Run:

```bash
git add backend/app/errors.py backend/app/exporter.py backend/app/main.py backend/tests/test_exporter.py backend/tests/test_api_export.py
git commit -m "feat: add excel export endpoint"
```

## Task 4: OCR Engine And Recognize API

**Files:**
- Create: `backend/app/ocr.py`
- Create: `backend/tests/test_api_recognize.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing recognize API tests**

Create `backend/tests/test_api_recognize.py`:

```python
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_engine
from app.models import RawOcrLine


class FakeEngine:
    def recognize(self, image_bytes: bytes) -> list[RawOcrLine]:
        assert image_bytes
        return [
            RawOcrLine(
                text="中心编号：B260112",
                confidence=0.93,
                box=[[1.0, 2.0], [3.0, 2.0], [3.0, 4.0], [1.0, 4.0]],
            ),
            RawOcrLine(
                text="试验前 1 281.25 281.15 279.05 285.348",
                confidence=0.88,
                box=[[1.0, 8.0], [500.0, 8.0], [500.0, 30.0], [1.0, 30.0]],
            ),
        ]


def png_bytes() -> bytes:
    image = Image.new("RGB", (64, 48), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_recognize_returns_structured_result() -> None:
    app.dependency_overrides[get_engine] = lambda: FakeEngine()
    client = TestClient(app)

    response = client.post(
        "/api/recognize",
        files={"file": ("sample.png", png_bytes(), "image/png")},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["documentType"] == "transformer_short_circuit_test_record"
    assert body["image"]["filename"] == "sample.png"
    assert body["image"]["width"] == 64
    assert body["image"]["height"] == 48
    assert body["fields"]["centerNumber"]["value"] == "B260112"
    assert body["tables"][0]["rows"][0]["AB"] == "281.25"
    assert body["rawOcr"][0]["text"] == "中心编号：B260112"


def test_recognize_rejects_non_image_file() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/recognize",
        files={"file": ("bad.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_file_type"
```

- [ ] **Step 2: Run recognize tests and verify they fail**

Run:

```bash
cd backend
pytest tests/test_api_recognize.py -v
```

Expected: FAIL because `/api/recognize`, `app.ocr`, and `get_engine` do not exist yet.

- [ ] **Step 3: Create OCR engine wrapper**

Create `backend/app/ocr.py`:

```python
from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.models import RawOcrLine


class OcrEngine(Protocol):
    def recognize(self, image_bytes: bytes) -> list[RawOcrLine]:
        pass


class PaddleOcrEngine:
    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(use_angle_cls=True, lang="ch")

    def recognize(self, image_bytes: bytes) -> list[RawOcrLine]:
        import cv2
        import numpy as np

        array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            return []

        result = self._ocr.ocr(image, cls=True)
        lines: list[RawOcrLine] = []
        for page in result or []:
            for item in page or []:
                box, text_info = item
                text, confidence = text_info
                lines.append(
                    RawOcrLine(
                        text=str(text),
                        confidence=float(confidence),
                        box=[[float(point[0]), float(point[1])] for point in box],
                    )
                )
        return lines


@lru_cache(maxsize=1)
def get_ocr_engine() -> OcrEngine:
    return PaddleOcrEngine()
```

- [ ] **Step 4: Add recognize route and file validation**

Replace `backend/app/main.py` with:

```python
from io import BytesIO

from fastapi import Depends, FastAPI, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

from app.errors import ApiError, api_error_handler
from app.exporter import build_workbook
from app.models import RecognitionResult, TemplateInfo
from app.ocr import OcrEngine, get_ocr_engine
from app.templates import DEFAULT_TEMPLATE_ID, get_template, template_infos

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="PaddleOCR Web Excel API")
app.add_exception_handler(ApiError, api_error_handler)


def get_engine() -> OcrEngine:
    return get_ocr_engine()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/templates", response_model=list[TemplateInfo])
def templates() -> list[TemplateInfo]:
    return template_infos()


@app.post("/api/recognize", response_model=RecognitionResult)
async def recognize(
    file: UploadFile = File(...),
    templateId: str = Form(DEFAULT_TEMPLATE_ID),
    engine: OcrEngine = Depends(get_engine),
) -> RecognitionResult:
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise ApiError(400, "unsupported_file_type", "Only JPEG, PNG, and WebP images are supported.", file.content_type or "")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise ApiError(400, "file_too_large", "Image file must be 10MB or smaller.", str(len(image_bytes)))

    try:
        image = Image.open(BytesIO(image_bytes))
        width, height = image.size
    except UnidentifiedImageError as exc:
        raise ApiError(400, "image_decode_failed", "Image cannot be decoded.", str(exc)) from exc

    try:
        template = get_template(templateId)
    except KeyError as exc:
        raise ApiError(400, "unknown_template", "Template is not supported.", templateId) from exc

    try:
        raw_lines = engine.recognize(image_bytes)
    except Exception as exc:
        raise ApiError(500, "ocr_failed", "OCR recognition failed.", str(exc)) from exc

    return template.extract(
        raw_lines=raw_lines,
        filename=file.filename or "uploaded-image",
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
```

- [ ] **Step 5: Run backend tests and verify they pass**

Run:

```bash
cd backend
pytest -v
```

Expected: PASS with all backend tests passing. The fake engine keeps tests independent from PaddleOCR model downloads.

- [ ] **Step 6: Commit OCR recognize API**

Run:

```bash
git add backend/app/ocr.py backend/app/main.py backend/tests/test_api_recognize.py
git commit -m "feat: add image recognize endpoint"
```

## Task 5: Frontend Skeleton, API Client, And Upload UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/setupTests.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Create frontend package and test configuration**

Create `frontend/package.json`:

```json
{
  "name": "paddleocr-web-excel-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "tsc && vite build",
    "test": "vitest run",
    "preview": "vite preview --host 127.0.0.1"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "latest",
    "@testing-library/react": "latest",
    "@testing-library/user-event": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "jsdom": "latest",
    "vitest": "latest"
  }
}
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PaddleOCR 表格识别</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
  },
});
```

Create `frontend/src/setupTests.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Add shared frontend API types**

Create `frontend/src/types.ts`:

```ts
export interface ImageInfo {
  filename: string;
  width: number;
  height: number;
}

export interface FieldValue {
  label: string;
  value: string;
  confidence: number;
  edited: boolean;
}

export interface TableData {
  id: string;
  title: string;
  columns: string[];
  rows: Record<string, string>[];
}

export interface RawOcrLine {
  text: string;
  confidence: number;
  box: number[][];
}

export interface WarningItem {
  code: string;
  message: string;
}

export interface RecognitionResult {
  documentType: string;
  image: ImageInfo;
  fields: Record<string, FieldValue>;
  tables: TableData[];
  rawOcr: RawOcrLine[];
  warnings: WarningItem[];
}

export interface TemplateInfo {
  id: string;
  name: string;
}
```

- [ ] **Step 3: Add typed API client**

Create `frontend/src/api.ts`:

```ts
import type { RecognitionResult, TemplateInfo } from "./types";

export async function fetchTemplates(): Promise<TemplateInfo[]> {
  const response = await fetch("/api/templates");
  if (!response.ok) {
    throw new Error("模板列表加载失败");
  }
  return response.json();
}

export async function recognizeDocument(file: File, templateId: string): Promise<RecognitionResult> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("templateId", templateId);

  const response = await fetch("/api/recognize", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "图片识别失败");
  }

  return response.json();
}

export async function exportWorkbook(result: RecognitionResult): Promise<Blob> {
  const response = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Excel 导出失败");
  }

  return response.blob();
}
```

- [ ] **Step 4: Write failing upload UI test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const recognition = {
  documentType: "transformer_short_circuit_test_record",
  image: { filename: "sample.png", width: 64, height: 48 },
  fields: {
    centerNumber: { label: "中心编号", value: "B260112", confidence: 0.93, edited: false },
  },
  tables: [
    {
      id: "before_test_reactance",
      title: "试验前电抗测量",
      columns: ["分接", "AB", "BC"],
      rows: [{ "分接": "1", AB: "281.25", BC: "281.15" }],
    },
  ],
  rawOcr: [{ text: "中心编号：B260112", confidence: 0.93, box: [[1, 2], [3, 2], [3, 4], [1, 4]] }],
  warnings: [],
};

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:preview"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/templates") {
          return new Response(JSON.stringify([{ id: "transformer_short_circuit_test_record", name: "变压器短路承受能力试验现场记录" }]));
        }
        if (url === "/api/recognize") {
          return new Response(JSON.stringify(recognition));
        }
        return new Response(null, { status: 404 });
      }),
    );
  });

  it("uploads an image and renders recognition results", async () => {
    render(<App />);
    const user = userEvent.setup();
    const file = new File(["image"], "sample.png", { type: "image/png" });

    await user.upload(screen.getByLabelText("上传表单照片"), file);
    await user.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByDisplayValue("B260112")).toBeInTheDocument();
    expect(screen.getByText("试验前电抗测量")).toBeInTheDocument();
    expect(screen.getByDisplayValue("281.25")).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Create app UI implementation**

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `frontend/src/App.tsx`:

```tsx
import { useEffect, useState } from "react";

import { fetchTemplates, recognizeDocument } from "./api";
import type { FieldValue, RecognitionResult, TemplateInfo } from "./types";

type Tab = "fields" | "tables" | "raw";

const DEFAULT_TEMPLATE_ID = "transformer_short_circuit_test_record";

function updateField(result: RecognitionResult, fieldId: string, value: string): RecognitionResult {
  const field: FieldValue = result.fields[fieldId];
  return {
    ...result,
    fields: {
      ...result.fields,
      [fieldId]: { ...field, value, edited: true },
    },
  };
}

function updateTableCell(
  result: RecognitionResult,
  tableIndex: number,
  rowIndex: number,
  columnName: string,
  value: string,
): RecognitionResult {
  return {
    ...result,
    tables: result.tables.map((table, currentTableIndex) => {
      if (currentTableIndex !== tableIndex) {
        return table;
      }
      return {
        ...table,
        rows: table.rows.map((row, currentRowIndex) =>
          currentRowIndex === rowIndex ? { ...row, [columnName]: value } : row,
        ),
      };
    }),
  };
}

export default function App() {
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [templateId, setTemplateId] = useState(DEFAULT_TEMPLATE_ID);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState<RecognitionResult | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("fields");
  const [status, setStatus] = useState("请选择一张表单照片");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchTemplates()
      .then((items) => {
        setTemplates(items);
        if (items[0]) {
          setTemplateId(items[0].id);
        }
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  useEffect(() => {
    if (!file) {
      setPreviewUrl("");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function handleRecognize() {
    if (!file) {
      setStatus("请先选择图片");
      return;
    }
    setBusy(true);
    setStatus("正在识别图片");
    try {
      const nextResult = await recognizeDocument(file, templateId);
      setResult(nextResult);
      setActiveTab("fields");
      setStatus("识别完成，可以校对后导出 Excel");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "图片识别失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>PaddleOCR 表格识别</h1>
          <p>上传现场记录照片，校对识别结果并导出 Excel。</p>
        </div>
        <button type="button" disabled>
          导出 Excel
        </button>
      </header>

      <section className="workspace">
        <aside className="image-panel">
          <label className="field-label" htmlFor="image-upload">
            上传表单照片
          </label>
          <input
            id="image-upload"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => {
              const nextFile = event.target.files?.[0] ?? null;
              setFile(nextFile);
              setResult(null);
              setStatus(nextFile ? "图片已选择，可以开始识别" : "请选择一张表单照片");
            }}
          />

          <label className="field-label" htmlFor="template-select">
            识别模板
          </label>
          <select id="template-select" value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>

          <button type="button" disabled={!file || busy} onClick={handleRecognize}>
            开始识别
          </button>
          <p className="status">{status}</p>

          <div className="preview-frame">
            {previewUrl ? <img src={previewUrl} alt="上传的表单预览" /> : <span>图片预览区</span>}
          </div>
        </aside>

        <section className="result-panel">
          <div className="tabs" role="tablist" aria-label="识别结果视图">
            <button type="button" className={activeTab === "fields" ? "active" : ""} onClick={() => setActiveTab("fields")}>
              关键字段
            </button>
            <button type="button" className={activeTab === "tables" ? "active" : ""} onClick={() => setActiveTab("tables")}>
              表格结果
            </button>
            <button type="button" className={activeTab === "raw" ? "active" : ""} onClick={() => setActiveTab("raw")}>
              原始OCR
            </button>
          </div>

          {!result && <div className="empty-state">识别完成后，结果会显示在这里。</div>}

          {result && activeTab === "fields" && (
            <div className="field-grid">
              {Object.entries(result.fields).map(([fieldId, field]) => (
                <label key={fieldId}>
                  <span>{field.label}</span>
                  <input value={field.value} onChange={(event) => setResult(updateField(result, fieldId, event.target.value))} />
                </label>
              ))}
            </div>
          )}

          {result && activeTab === "tables" && (
            <div className="table-stack">
              {result.tables.map((table, tableIndex) => (
                <section key={table.id}>
                  <h2>{table.title}</h2>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          {table.columns.map((column) => (
                            <th key={column}>{column}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.rows.map((row, rowIndex) => (
                          <tr key={`${table.id}-${rowIndex}`}>
                            {table.columns.map((column) => (
                              <td key={column}>
                                <input
                                  value={row[column] ?? ""}
                                  onChange={(event) =>
                                    setResult(updateTableCell(result, tableIndex, rowIndex, column, event.target.value))
                                  }
                                />
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ))}
            </div>
          )}

          {result && activeTab === "raw" && (
            <ol className="raw-list">
              {result.rawOcr.map((line, index) => (
                <li key={`${line.text}-${index}`}>
                  <span>{line.text}</span>
                  <strong>{Math.round(line.confidence * 100)}%</strong>
                </li>
              ))}
            </ol>
          )}
        </section>
      </section>
    </main>
  );
}
```

Create `frontend/src/styles.css`:

```css
:root {
  color: #172026;
  background: #f4f6f8;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input,
select {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 28px;
  background: #ffffff;
  border-bottom: 1px solid #d8dee6;
}

.topbar h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.3;
}

.topbar p {
  margin: 4px 0 0;
  color: #5e6b78;
}

button {
  border: 1px solid #2f6fed;
  border-radius: 6px;
  padding: 9px 14px;
  color: #ffffff;
  background: #2f6fed;
  cursor: pointer;
}

button:disabled {
  border-color: #b9c2cf;
  background: #b9c2cf;
  cursor: not-allowed;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(320px, 38vw) minmax(0, 1fr);
  gap: 20px;
  padding: 20px;
}

.image-panel,
.result-panel {
  min-height: calc(100vh - 104px);
  padding: 18px;
  background: #ffffff;
  border: 1px solid #d8dee6;
  border-radius: 8px;
}

.image-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label {
  font-weight: 700;
}

input,
select {
  width: 100%;
  border: 1px solid #c8d0da;
  border-radius: 6px;
  padding: 8px 10px;
  background: #ffffff;
}

.status {
  min-height: 22px;
  margin: 0;
  color: #50606f;
}

.preview-frame {
  display: grid;
  min-height: 420px;
  place-items: center;
  overflow: hidden;
  color: #667789;
  background: #eef2f5;
  border: 1px dashed #aeb8c5;
  border-radius: 8px;
}

.preview-frame img {
  display: block;
  max-width: 100%;
  max-height: 72vh;
  object-fit: contain;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tabs button {
  color: #24313d;
  background: #edf1f5;
  border-color: #d8dee6;
}

.tabs button.active {
  color: #ffffff;
  background: #2f6fed;
  border-color: #2f6fed;
}

.empty-state {
  display: grid;
  min-height: 320px;
  place-items: center;
  color: #667789;
  border: 1px dashed #c8d0da;
  border-radius: 8px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.field-grid label span {
  display: block;
  margin-bottom: 6px;
  font-weight: 700;
}

.table-stack {
  display: grid;
  gap: 20px;
}

.table-stack h2 {
  margin: 0 0 10px;
  font-size: 17px;
}

.table-scroll {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  min-width: 120px;
  border: 1px solid #d8dee6;
  padding: 6px;
  text-align: left;
}

th {
  background: #edf1f5;
}

.raw-list {
  display: grid;
  gap: 8px;
  padding-left: 22px;
}

.raw-list li {
  padding: 8px 10px;
  background: #f6f8fa;
  border: 1px solid #d8dee6;
  border-radius: 6px;
}

.raw-list strong {
  margin-left: 10px;
  color: #2f6fed;
}

@media (max-width: 900px) {
  .topbar,
  .workspace {
    grid-template-columns: 1fr;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .workspace {
    display: grid;
  }
}
```

- [ ] **Step 6: Run frontend test and verify it passes**

Run:

```bash
cd frontend
npm test
```

Expected: PASS with the upload UI test passing.

- [ ] **Step 7: Build frontend and verify it passes**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS with TypeScript and Vite build succeeding.

- [ ] **Step 8: Commit frontend upload workflow**

Run:

```bash
git add frontend
git commit -m "feat: add frontend upload workflow"
```

## Task 6: Export Interaction Test And Download Flow

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Extend frontend test for edited export**

Replace `frontend/src/App.test.tsx` with:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const recognition = {
  documentType: "transformer_short_circuit_test_record",
  image: { filename: "sample.png", width: 64, height: 48 },
  fields: {
    centerNumber: { label: "中心编号", value: "B260112", confidence: 0.93, edited: false },
  },
  tables: [
    {
      id: "before_test_reactance",
      title: "试验前电抗测量",
      columns: ["分接", "AB", "BC"],
      rows: [{ "分接": "1", AB: "281.25", BC: "281.15" }],
    },
  ],
  rawOcr: [{ text: "中心编号：B260112", confidence: 0.93, box: [[1, 2], [3, 2], [3, 4], [1, 4]] }],
  warnings: [],
};

describe("App", () => {
  beforeEach(() => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:local"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url === "/api/templates") {
          return new Response(JSON.stringify([{ id: "transformer_short_circuit_test_record", name: "变压器短路承受能力试验现场记录" }]));
        }
        if (url === "/api/recognize") {
          return new Response(JSON.stringify(recognition));
        }
        if (url === "/api/export") {
          const body = JSON.parse(String(init?.body));
          expect(body.fields.centerNumber.value).toBe("B260113");
          expect(body.fields.centerNumber.edited).toBe(true);
          return new Response(new Blob(["xlsx"]));
        }
        return new Response(null, { status: 404 });
      }),
    );
  });

  it("uploads an image and renders recognition results", async () => {
    render(<App />);
    const user = userEvent.setup();
    const file = new File(["image"], "sample.png", { type: "image/png" });

    await user.upload(screen.getByLabelText("上传表单照片"), file);
    await user.click(screen.getByRole("button", { name: "开始识别" }));

    expect(await screen.findByDisplayValue("B260112")).toBeInTheDocument();
    expect(screen.getByText("试验前电抗测量")).toBeInTheDocument();
    expect(screen.getByDisplayValue("281.25")).toBeInTheDocument();
  });

  it("exports edited recognition data", async () => {
    render(<App />);
    const user = userEvent.setup();
    const file = new File(["image"], "sample.png", { type: "image/png" });

    await user.upload(screen.getByLabelText("上传表单照片"), file);
    await user.click(screen.getByRole("button", { name: "开始识别" }));
    await user.clear(await screen.findByDisplayValue("B260112"));
    await user.type(screen.getByLabelText("中心编号"), "B260113");
    await user.click(screen.getByRole("button", { name: "导出 Excel" }));

    expect(await screen.findByText("Excel 已生成")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run frontend test and verify the accessible label failure**

Run:

```bash
cd frontend
npm test
```

Expected: FAIL because the UI has no enabled export action yet, so the status text `Excel 已生成` never appears.

- [ ] **Step 3: Add export download behavior**

In `frontend/src/App.tsx`, change the first two import statements to:

```tsx
import { useEffect, useMemo, useState } from "react";

import { exportWorkbook, fetchTemplates, recognizeDocument } from "./api";
```

Add this value below the `useEffect` hooks:

```tsx
  const canExport = useMemo(() => result !== null && !busy, [busy, result]);
```

Add this function below `handleRecognize`:

```tsx
  async function handleExport() {
    if (!result) {
      return;
    }
    setBusy(true);
    setStatus("正在生成 Excel");
    try {
      const blob = await exportWorkbook(result);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "recognition-result.xlsx";
      link.click();
      URL.revokeObjectURL(url);
      setStatus("Excel 已生成");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Excel 导出失败");
    } finally {
      setBusy(false);
    }
  }
```

Replace the export button with:

```tsx
        <button type="button" disabled={!canExport} onClick={handleExport}>
          导出 Excel
        </button>
```

- [ ] **Step 4: Run frontend tests and build**

Run:

```bash
cd frontend
npm test
npm run build
```

Expected: PASS for tests and build.

- [ ] **Step 5: Commit export interaction coverage**

Run:

```bash
git add frontend/src/App.test.tsx frontend/src/App.tsx
git commit -m "test: cover edited excel export flow"
```

## Task 7: Project Documentation And Local Run Commands

**Files:**
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Add gitignore**

Create `.gitignore`:

```gitignore
.DS_Store
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
dist/
build/
node_modules/
frontend/dist/
*.xlsx
```

- [ ] **Step 2: Add README**

Create `README.md`:

```markdown
# PaddleOCR Starter

Local web app for recognizing photographed transformer short-circuit test record forms and exporting corrected recognition results to Excel.

## Scope

Version 1 targets the fixed form type `变压器短路承受能力试验现场记录`.

The workflow is:

1. Open the local web page.
2. Upload a form photo.
3. Run OCR through the local FastAPI backend.
4. Review and edit key fields and table values.
5. Export an `.xlsx` workbook.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run backend tests:

```bash
cd backend
pytest -v
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Run frontend tests:

```bash
cd frontend
npm test
npm run build
```

## API

- `GET /api/health`
- `GET /api/templates`
- `POST /api/recognize`
- `POST /api/export`

## Notes

PaddleOCR model loading can take time on the first recognition request. Automated backend tests use a fake OCR engine so tests do not require model downloads.
```

- [ ] **Step 3: Run full available verification**

Run:

```bash
cd backend
pytest -v
cd ../frontend
npm test
npm run build
```

Expected: all backend tests pass, all frontend tests pass, and frontend build succeeds.

- [ ] **Step 4: Commit docs and ignore rules**

Run:

```bash
git add .gitignore README.md
git commit -m "docs: add local development guide"
```

## Task 8: Manual End-To-End Verification

**Files:**
- No source files should be changed unless verification exposes a defect.

- [ ] **Step 1: Start backend**

Run:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected: server listens on `http://127.0.0.1:8000`.

- [ ] **Step 2: Start frontend**

Run in a second terminal:

```bash
cd frontend
npm run dev
```

Expected: Vite serves the app at `http://127.0.0.1:5173`.

- [ ] **Step 3: Verify the browser workflow**

Open `http://127.0.0.1:5173` and perform these checks:

1. Upload the provided sample photo.
2. Confirm the preview image appears in the left panel.
3. Click `开始识别`.
4. Confirm key fields, table rows, and raw OCR appear.
5. Edit `中心编号` to a visible changed value.
6. Click `导出 Excel`.
7. Open the downloaded workbook.
8. Confirm the workbook contains sheets `识别结果`, `关键字段`, and `原始OCR`.
9. Confirm the edited `中心编号` value appears in the workbook.

- [ ] **Step 4: Record manual verification result**

If the workflow succeeds, add a short dated note to `README.md` under a `Manual Verification` heading:

```markdown
## Manual Verification

- 2026-06-14: Uploaded the sample transformer test record photo locally, reviewed recognized fields and tables, edited a field, exported Excel, and confirmed the edited value appeared in the workbook.
```

- [ ] **Step 5: Commit manual verification note**

Run:

```bash
git add README.md
git commit -m "docs: record manual verification"
```

## Self-Review

Spec coverage:

- Local web page upload: Task 5.
- FastAPI backend: Tasks 1, 3, and 4.
- PaddleOCR recognition: Task 4.
- Fixed template extraction: Task 2.
- Editable fields and tables: Tasks 5 and 6.
- Raw OCR view: Task 5.
- Excel workbook export: Task 3 plus Task 6.
- Supported templates endpoint: Task 2.
- Error envelope: Tasks 3 and 4.
- Manual end-to-end verification: Task 8.

Placeholder scan:

- The plan uses concrete file paths, code blocks, commands, and expected outcomes.
- No task relies on unspecified implementation work.

Type consistency:

- Backend response fields use `documentType`, `rawOcr`, `fields`, `tables`, and `warnings`.
- Frontend `RecognitionResult` mirrors backend `RecognitionResult`.
- Export endpoint accepts the same edited recognition shape that recognize returns.
