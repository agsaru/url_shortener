from fastapi import FastAPI
from configs.db import engine, Base
from models.model import Url 
from routes.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")
app.include_router(router)
@app.get("/")
def hello():
    return {"message": "Backend is running"}
