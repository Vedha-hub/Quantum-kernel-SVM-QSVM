"""FastAPI backend. Run from the project root:

    uvicorn backend.main:app --reload

Open http://127.0.0.1:8000        -> the frontend
Open http://127.0.0.1:8000/docs   -> automatic API documentation
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import RunRequest, SweepRequest
from .services.data import list_datasets
from .services.evaluate import run_experiment, run_sweep
from .services.quantum import FEATURE_MAPS
from .storage import load_history, save_run

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="QSVM Lab API", version="1.0.0")

# Lets a frontend served from another port (e.g. VS Code Live Server) call the API.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/options")
def options():
    return {
        "datasets": list_datasets(),
        "feature_maps": [{"name": k, "description": v} for k, v in FEATURE_MAPS.items()],
    }


@app.post("/api/run")
def run(req: RunRequest):
    try:
        result = run_experiment(**req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    save_run(result)
    return result


@app.post("/api/sweep")
def sweep(req: SweepRequest):
    try:
        return run_sweep(**req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/history")
def history(limit: int = 50):
    return load_history(limit)


# Frontend is served last so it never hides the /api routes.
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")
