from fastapi import FastAPI
from app.routers.biomarkers import router as biomarker_router

app = FastAPI(title="CareMinder Backend")

@app.get("/") #root RestFul API endpoint created while first deployment on render so that Fast Api had an end point to run on and test the deployment. It can be removed or modified as needed.
def root():
    return {"message": "CareMinder backend is running wild"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(biomarker_router)