from fastapi import FastAPI
from src.routes.routes import router

app = FastAPI(title="URL Shortener")
app.include_router(router)
@app.get("/")
def hello():
    return {"message": "Backend is running"}
