from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_URLS
from routes.scan_routes import router

app = FastAPI(title="AI GitHub Repository Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "AI GitHub Repository Scanner API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
