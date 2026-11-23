from fastapi import FastAPI


app = FastAPI(
    title="Print Models API",
    description="REST API за каталог на 3D модели за печат.",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
