# PaddleOCR Web Excel Design

## Goal

Build a local web application that accepts a photographed transformer short-circuit test record form, recognizes the form content with PaddleOCR, lets the user review the extracted result, and exports a corresponding Excel file.

The first version targets one fixed form type: `变压器短路承受能力试验现场记录`. Later versions can add template management for other form layouts.

## Success Criteria

- A user can open a local web page and upload a form photo.
- The system recognizes printed Chinese text, handwritten numeric table values, check marks, and key metadata where possible.
- The web page shows the original image beside editable recognition results.
- The user can export an `.xlsx` workbook that preserves the important table and field structure.
- Raw OCR output is retained for troubleshooting.
- The design leaves a clear path for adding more templates later.

## Non-Goals For Version 1

- Cloud deployment.
- Multi-user accounts or permission management.
- Database persistence.
- Fully automatic recognition with no manual correction.
- Universal OCR for arbitrary documents.
- Full template editor UI.

## Product Flow

1. User opens the local web app.
2. User uploads a photographed form image.
3. Frontend previews the uploaded image.
4. Frontend sends the image to the local FastAPI backend.
5. Backend preprocesses the image and runs PaddleOCR.
6. Backend maps OCR results into a fixed form schema.
7. Frontend displays editable structured results.
8. User corrects recognition mistakes.
9. User clicks export.
10. Backend generates and returns an Excel file.

## Application Architecture

### Frontend

Use React, Vite, and TypeScript.

Responsibilities:

- Image upload.
- Image preview.
- Recognition status display.
- Editable key fields.
- Editable table sections.
- Raw OCR view for debugging.
- Export Excel trigger.
- Clear error messages when recognition or export fails.

The first screen should be the usable workflow, not a landing page.

### Backend

Use FastAPI.

Responsibilities:

- Receive uploaded image files.
- Validate file type and size.
- Run preprocessing with OpenCV.
- Run PaddleOCR recognition.
- Apply fixed-template extraction rules.
- Return structured JSON to the frontend.
- Generate Excel files with `openpyxl`.

### OCR Layer

Use PaddleOCR Chinese recognition models for initial OCR.

Version 1 will combine whole-image OCR with template-aware region extraction. The template logic can start simple and become more precise as test images accumulate.

### Template Layer

Version 1 has one built-in template definition for `变压器短路承受能力试验现场记录`.

The template should define:

- Template id and name.
- Key field names.
- Table section names.
- Expected rows and columns.
- Optional region-of-interest coordinates once enough sample images are available.
- Post-processing rules for numeric values, dates, and check marks.

The code should keep this template separate from generic OCR and export code so later templates can be added without rewriting the app.

## Data Model

The backend recognition response should use this shape:

```json
{
  "documentType": "transformer_short_circuit_test_record",
  "image": {
    "filename": "sample.jpg",
    "width": 1080,
    "height": 1920
  },
  "fields": {
    "centerNumber": {
      "label": "中心编号",
      "value": "B260112",
      "confidence": 0.93
    },
    "client": {
      "label": "委托单位",
      "value": "山东鲁能泰山电力设备有限公司",
      "confidence": 0.91
    }
  },
  "tables": [
    {
      "id": "before_test_reactance",
      "title": "试验前电抗测量",
      "columns": ["分接", "AB", "BC", "CA", "电抗(mH)"],
      "rows": [
        {
          "分接": "1",
          "AB": "281.25",
          "BC": "281.15",
          "CA": "279.05",
          "电抗(mH)": "285.348"
        }
      ]
    }
  ],
  "rawOcr": [
    {
      "text": "变压器短路承受能力试验现场记录",
      "confidence": 0.98,
      "box": [[292, 323], [739, 323], [739, 360], [292, 360]]
    }
  ],
  "warnings": [
    {
      "code": "low_confidence",
      "message": "部分手写数字置信度较低，请人工确认。"
    }
  ]
}
```

The frontend may edit `fields` and `tables` before export. Edited data should be submitted to the export endpoint so the generated Excel matches the corrected result.

## Excel Output

Generate one `.xlsx` workbook with these sheets:

### 识别结果

Contains the main form data in a layout close to the source document. This is the primary sheet the user will keep.

It should include:

- Title.
- Key metadata fields.
- `试验前` table.
- `试验过程中` table.
- `试验后` table.
- Right-side site condition values and check marks where recognized.
- Date/signature fields if recognized.

### 关键字段

Contains normalized key-value pairs for easier review and downstream import.

Example columns:

- Field id.
- Field label.
- Value.
- Confidence.
- User edited flag.

### 原始OCR

Contains raw PaddleOCR output for troubleshooting.

Example columns:

- Text.
- Confidence.
- Box coordinates.
- Source region if known.

## API Design

### `POST /api/recognize`

Accepts multipart form data:

- `file`: uploaded image.
- `templateId`: optional, defaults to the transformer test record template.

Returns the structured recognition JSON.

### `POST /api/export`

Accepts edited recognition JSON.

Returns an `.xlsx` file download.

### `GET /api/templates`

Returns the list of supported templates. Version 1 can return only one template.

## Error Handling

Frontend should show clear messages for:

- Unsupported file type.
- File too large.
- OCR model not installed or not loaded.
- Image cannot be decoded.
- Recognition succeeds but confidence is low.
- Excel generation fails.

Backend should return structured error responses:

```json
{
  "error": {
    "code": "ocr_failed",
    "message": "OCR recognition failed.",
    "detail": "..."
  }
}
```

## Accuracy Strategy

Version 1 should prioritize usable workflow and correction over perfect recognition.

Initial recognition strategy:

- Run PaddleOCR on the whole image.
- Group OCR lines by location.
- Extract obvious key fields through labels and nearby text.
- Populate known tables using fixed row and column expectations.
- Mark uncertain or missing values with warnings.

Improvement path:

- Add document boundary detection and perspective correction.
- Add region-of-interest OCR for fixed template areas.
- Add numeric post-processing for handwritten values.
- Add check mark detection for checkbox columns.
- Highlight low-confidence cells in the UI.
- Collect sample images and expected Excel output for regression tests.

## UI Design

The application should open directly into the OCR workflow:

- Top bar with app name and template selector.
- Left panel for image upload and preview.
- Right panel for recognition results.
- Tabs or segmented controls for `关键字段`, `表格结果`, and `原始OCR`.
- Primary export button once recognition data exists.

The UI should be compact and work-focused. It should feel like an internal inspection tool, not a marketing website.

## Testing Plan

Backend tests:

- Recognition response schema can be created from sample OCR data.
- Template parser maps OCR text into expected fields and tables.
- Export endpoint creates a valid `.xlsx` workbook.
- Error responses are structured consistently.

Frontend tests:

- Upload state transitions.
- Recognition result rendering.
- Editable fields and table cells.
- Export button submits edited data.

Manual verification:

- Upload the provided sample photo.
- Confirm key fields are visible.
- Correct a few cells manually.
- Export Excel.
- Open the workbook and verify the edited values appear in the expected sheets.

## Implementation Phases

### Phase 1: Project Skeleton

- Create FastAPI backend.
- Create React/Vite frontend.
- Add development scripts and README.
- Add basic health endpoint.

### Phase 2: Upload And Raw OCR

- Add image upload UI.
- Add `/api/recognize`.
- Run PaddleOCR and return raw OCR lines.
- Display raw OCR text in the frontend.

### Phase 3: Fixed Template Extraction

- Add transformer test record template schema.
- Extract key fields and table sections.
- Display editable structured results.

### Phase 4: Excel Export

- Add `/api/export`.
- Generate workbook sheets: `识别结果`, `关键字段`, `原始OCR`.
- Download generated `.xlsx` from the browser.

### Phase 5: Accuracy Improvements

- Add image preprocessing.
- Add low-confidence warnings.
- Add manual correction UX polish.
- Add sample-based regression tests.

## Open Assumptions

- The app will run locally on the user's machine.
- The backend may install and load PaddleOCR locally.
- The first supported template is the sample transformer test record form.
- Manual correction before export is acceptable for Version 1.
- Generated Excel is the primary deliverable.
