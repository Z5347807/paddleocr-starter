from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ocr import recognize_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run OCR on an image with PaddleOCR.")
    parser.add_argument("image", type=Path, help="Path to the image file.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print formatted JSON output.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = recognize_image(args.image)
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()

