from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.exceptions import AppError
from backend.routes import router


app = FastAPI(
    title="Print Models API",
    description="REST API за каталог на 3D модели за печат.",
    version="0.5.0",
)
app.include_router(router)
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": details})


@app.exception_handler(AppError)
def handle_exception(request: Request, error: AppError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content={"message": error.message})


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
