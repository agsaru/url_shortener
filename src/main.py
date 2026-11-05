from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.configs.limiter import limiter
from src.routes.routes import router

app = FastAPI(title="URL Shortener")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    fields = {error["loc"][-1] for error in exc.errors() if error.get("loc")}

    if "custom_alias" in fields:
        message = (
            "Aliases can only contain letters, numbers, underscores, and "
            "hyphens, and must be 64 characters or fewer."
        )
    elif "longUrl" in fields:
        message = "Please provide a valid URL using HTTP or HTTPS."
    else:
        message = "Please check your request and try again."

    return JSONResponse(
        status_code=422,
        content={"detail": message},
    )


app.include_router(router)


@app.get("/")
def hello():
    return {"message": "Backend is running"}
