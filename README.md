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

The backend uses Python 3.10-3.12 because the PaddleOCR/PaddlePaddle runtime is not stable on newer Python releases.

```bash
cd backend
uv run --extra dev uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run backend tests:

```bash
cd backend
uv run --extra dev pytest -v
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

## Manual Verification

- 2026-06-14: Uploaded the sample transformer test record photo locally, reviewed recognized fields, edited `中心编号` to `B260113`, exported Excel, and confirmed the edited value appeared in workbook sheets `识别结果` and `关键字段`.
