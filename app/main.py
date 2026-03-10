from fastapi import FastAPI
from app.routers.biomarkers import router as biomarker_router

app = FastAPI(title="CareMinder Backend")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "CareMinder backend running"}

app.include_router(biomarker_router)