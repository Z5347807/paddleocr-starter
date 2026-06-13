from fastapi import FastAPI

app = FastAPI(title="PaddleOCR Web Excel API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
