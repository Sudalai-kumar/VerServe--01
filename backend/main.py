from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from routers import impact, auth, requests, uploads, chat

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)


# ── Lifespan — (Formerly for scheduler) ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan hook for Prototype 2: Hyper-local Help."""
    yield


app = FastAPI(
    title="GoodNeighbor Prototype 2",
    description="Hyper-local Mutual Aid — Connect and help your neighbors in Chennai.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS — allow React dev server ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(impact.router)
app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(uploads.router)
app.include_router(chat.router)

# Mount static files for uploads
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", tags=["root"])
def root():
    return {
        "app": "GoodNeighbor P2P Help",
        "version": "2.0.0",
        "description": "Hyper-local Help and Mutual Aid for Chennai.",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
def health():
    return {"status": "ok", "service": "GoodNeighbor API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
