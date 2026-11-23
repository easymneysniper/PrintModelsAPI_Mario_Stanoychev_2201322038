from fastapi import FastAPI

from backend.routes import router


app = FastAPI(
    title="Print Models API",
    description="REST API за каталог на 3D модели за печат.",
    version="0.2.0",
)
app.include_router(router)


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
