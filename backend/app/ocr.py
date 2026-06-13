from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.models import RawOcrLine


class OcrEngine(Protocol):
    def recognize(self, image_bytes: bytes) -> list[RawOcrLine]:
        pass


def _box_to_points(box) -> list[list[float]]:
    if box is None:
        return []
    if hasattr(box, "tolist"):
        box = box.tolist()
    if box and isinstance(box[0], (int, float)):
        x1, y1, x2, y2 = [float(value) for value in box[:4]]
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return [[float(point[0]), float(point[1])] for point in box]


def _lines_from_predict_result(result) -> list[RawOcrLine]:
    lines: list[RawOcrLine] = []
    for page in result or []:
        data = dict(page) if isinstance(page, dict) else getattr(page, "json", None)
        if callable(data):
            data = data()
        if not isinstance(data, dict):
            continue

        texts = data.get("rec_texts") or []
        scores = data.get("rec_scores") or []
        boxes = data.get("rec_polys") or data.get("dt_polys") or data.get("rec_boxes") or []
        for index, text in enumerate(texts):
            score = scores[index] if index < len(scores) else 0.0
            box = boxes[index] if index < len(boxes) else []
            lines.append(RawOcrLine(text=str(text), confidence=float(score), box=_box_to_points(box)))
    return lines


def _lines_from_legacy_result(result) -> list[RawOcrLine]:
    lines: list[RawOcrLine] = []
    for page in result or []:
        for item in page or []:
            box, text_info = item
            text, confidence = text_info
            lines.append(
                RawOcrLine(
                    text=str(text),
                    confidence=float(confidence),
                    box=_box_to_points(box),
                )
            )
    return lines


class PaddleOcrEngine:
    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
        )

    def recognize(self, image_bytes: bytes) -> list[RawOcrLine]:
        import cv2
        import numpy as np

        array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            return []

        if hasattr(self._ocr, "predict"):
            return _lines_from_predict_result(self._ocr.predict(image))

        return _lines_from_legacy_result(self._ocr.ocr(image, cls=True))


@lru_cache(maxsize=1)
def get_ocr_engine() -> OcrEngine:
    return PaddleOcrEngine()
