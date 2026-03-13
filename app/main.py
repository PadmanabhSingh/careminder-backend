from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers.biomarkers import router as biomarker_router
from app.routers.alerts import router as alerts_router
from app.routers.devices import router as devices_router
from app.routers.auth import router as auth_router
from app.routers.providers import router as provider_router
from app.routers.reports import router as reports_router

app = FastAPI(title="CareMinder Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error"
        }
    )


@app.get("/")
def root():
    return {
        "service": "CareMinder API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(biomarker_router)
app.include_router(alerts_router)
app.include_router(devices_router)
app.include_router(provider_router)
app.include_router(reports_router)