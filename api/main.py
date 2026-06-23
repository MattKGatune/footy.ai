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
    import api.db as db
    import os
    ext_files = []
    try:
        for root, _, files in os.walk(db._EXT_DIR):
            ext_files += [os.path.join(root, f) for f in files]
    except Exception:
        pass
    cached_files = 0
    try:
        for _, _, files in os.walk(db._CACHE_DIR):
            cached_files += len(files)
    except Exception:
        pass
    return {
        "mcon_ready": db._mcon is not None,
        "matches_event_set": db._matches_ready.is_set(),
        "events_event_set": db._events_ready.is_set(),
        "event_file_count": len(db._event_key_map),
        "schema_anchor": db._schema_anchor,
        "cached_files": cached_files,
        "init_error": db._init_error,
        "ext_dir": db._EXT_DIR,
        "ext_files": ext_files,
    }


frontend = Path(__file__).parent.parent / "frontend"
if (frontend / "index.html").exists():
    app.mount("/ui", StaticFiles(directory=str(frontend), html=True), name="frontend")

client_dist = Path(__file__).parent.parent / "client" / "dist"
if (client_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(client_dist), html=True), name="client")
