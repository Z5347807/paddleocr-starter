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
