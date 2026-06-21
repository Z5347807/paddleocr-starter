from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from paddleocr import PaddleOCR


@lru_cache(maxsize=1)
def get_ocr_engine() -> PaddleOCR:
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="ch",
        device="cpu",
    )


def recognize_image(image_path: str | Path) -> list[dict[str, Any]]:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    pages = get_ocr_engine().predict(str(path))
    results: list[dict[str, Any]] = []

    for page in pages:
        page_data = _as_mapping(page)
        result_data = page_data.get("res", page_data)
        texts = result_data.get("rec_texts", [])
        scores = _to_plain(result_data.get("rec_scores", []))
        boxes = _to_plain(result_data.get("rec_polys", result_data.get("dt_polys", [])))

        for index, text in enumerate(texts):
            if not text:
                continue
            score = scores[index] if index < len(scores) else None
            box = boxes[index] if index < len(boxes) else None
            results.append({"text": text, "score": score, "box": box})

    return results


def _as_mapping(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "keys"):
        return dict(result)
    if hasattr(result, "res"):
        return {"res": result.res}
    raise TypeError(f"Unsupported PaddleOCR result type: {type(result)!r}")


def _to_plain(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value
