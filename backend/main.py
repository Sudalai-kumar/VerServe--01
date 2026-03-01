from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routers import opportunities, ngos, impact, auth
from routers.scraper_admin import router as scraper_router
from scheduler import start_scheduler, stop_scheduler

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)


# ── Lifespan — start/stop background scheduler ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: launch scraper scheduler.  Shutdown: gracefully stop it."""
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="VeriServe API",
    description="Verified Volunteering Aggregator for Chennai — powered by the Trust Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS — allow React dev server ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(opportunities.router)
app.include_router(ngos.router)
app.include_router(impact.router)
app.include_router(auth.router)
app.include_router(scraper_router)


@app.get("/", tags=["root"])
def root():
    return {
        "app": "VeriServe Chennai",
        "version": "1.0.0",
        "description": "Verified Volunteering Aggregator — Trust Engine powered",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
def health():
    return {"status": "ok", "service": "VeriServe API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
