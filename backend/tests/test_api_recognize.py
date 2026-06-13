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
