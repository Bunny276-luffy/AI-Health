from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analysis

app = FastAPI(
    title="Uncertainty-Aware AI Tumor Detection API",
    description="Backend API for processing medical scans, simulating tumor detection, and estimating model uncertainty.",
    version="1.0.0"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"status": "online", "message": "NeuroScan Core API Running"}
