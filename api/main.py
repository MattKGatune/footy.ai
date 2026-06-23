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


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "redis": REDIS_AVAILABLE}


@app.get("/debug")
def debug():
    from api.db import _mcon, _con, _matches_ready, _events_ready, _init_error, _EXT_DIR
    import os
    ext_files = []
    try:
        for root, _, files in os.walk(_EXT_DIR):
            ext_files += [os.path.join(root, f) for f in files]
    except Exception:
        pass
    return {
        "mcon_ready": _mcon is not None,
        "con_ready": _con is not None,
        "matches_event_set": _matches_ready.is_set(),
        "events_event_set": _events_ready.is_set(),
        "init_error": _init_error,
        "ext_dir": _EXT_DIR,
        "ext_files": ext_files,
    }


frontend = Path(__file__).parent.parent / "frontend"
if (frontend / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=str(frontend), html=True), name="frontend")

client_dist = Path(__file__).parent.parent / "client" / "dist"
if (client_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(client_dist), html=True), name="client")
