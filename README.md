# PaddleOCR Starter

A small Python project that uses [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for image OCR.

It includes:

- A command line OCR tool
- A FastAPI HTTP endpoint
- Docker support
- A simple project layout that is ready to push to GitHub

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m paddleocr_starter.cli path/to/image.png --pretty
```

The first run downloads PaddleOCR model files automatically.

Use Python 3.9 through 3.13. PaddlePaddle wheels are not available for every
new Python release immediately.

## HTTP API

Start the API:

```bash
uvicorn paddleocr_starter.api:app --host 0.0.0.0 --port 8000
```

Send an image:

```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@path/to/image.png"
```

## Docker

```bash
docker build -t paddleocr-starter .
docker run --rm -p 8000:8000 paddleocr-starter
```

## Project Structure

```text
.
|-- src/paddleocr_starter/
|   |-- api.py
|   |-- cli.py
|   `-- ocr.py
|-- requirements.txt
|-- Dockerfile
`-- README.md
```

## Notes

- This starter is configured for CPU usage.
- For production workloads, pin model versions and tune PaddleOCR initialization options for your language and hardware.
- If you need Chinese text recognition, keep `lang="ch"` in `src/paddleocr_starter/ocr.py`.
