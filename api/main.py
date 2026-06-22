from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routers import chat, matches, narrative, shots, timeline
from api.cache import REDIS_AVAILABLE

app = FastAPI(title="footy.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches.router)
app.include_router(shots.router)
app.include_router(timeline.router)
app.include_router(narrative.router)
app.include_router(chat.router)

frontend = Path(__file__).parent.parent / "frontend"
if (frontend / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=str(frontend), html=True), name="frontend")

client_dist = Path(__file__).parent.parent / "client" / "dist"
if (client_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(client_dist), html=True), name="client")


@app.get("/health")
def health():
    return {"status": "ok", "redis": REDIS_AVAILABLE}
