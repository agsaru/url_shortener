from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.configs.limiter import limiter
from src.routes.routes import router

app = FastAPI(title="URL Shortener")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)

@app.get("/")
def hello():
    return {"message": "Backend is running"}