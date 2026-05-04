from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis, vqa, comparison

app = FastAPI(
    title="NeuroScan — Uncertainty-Aware AI Tumor Detection API",
    description=(
        "Production API: MC Dropout ensemble inference, conformal prediction, "
        "multi-organ routing, radiomics, VQA, temporal comparison, federated learning."
    ),
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1")
app.include_router(vqa.router, prefix="/api/v1")
app.include_router(comparison.router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict:
    return {"status": "online", "message": "NeuroScan Core API v2.0 Running"}
