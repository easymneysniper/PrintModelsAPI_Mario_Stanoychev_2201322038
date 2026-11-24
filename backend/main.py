from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.routes import router


app = FastAPI(
    title="Print Models API",
    description="REST API за каталог на 3D модели за печат.",
    version="0.3.0",
)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        {"type": item["type"], "loc": item["loc"], "msg": item["msg"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": details})


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {"status": "ok"}
