from fastapi import FastAPI
from app.routers.biomarkers import router as biomarker_router
from app.routers.alerts import router as alerts_router

app = FastAPI(title="CareMinder Backend")


@app.get("/")
def root():
    return {"message": "CareMinder backend running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(biomarker_router)
app.include_router(alerts_router)