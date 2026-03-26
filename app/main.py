from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers.biomarkers import router as biomarker_router
from app.routers.alerts import router as alerts_router
from app.routers.devices import router as devices_router
from app.routers.auth import router as auth_router
from app.routers.providers import router as provider_router
from app.routers.reports import router as reports_router
from app.routers.weather import router as weather_router
from app.routers.withings import router as withings_router
from app.routers.users import router as users_router
from app.routers.specialists import router as specialists_router
from app.routers.appointments import router as apointments_router
from app.routers.achievements import router as achievements_router
from app.routers.chat import router as chat_router
from app.routers.fitness import router as fitness_router    
from app.routers.dashboard import router as dashboard_router

app = FastAPI(title="CareMinder Backend")

origins = [
    ["*"], # allows all origins 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

@app.get("/reset-password")
def reset_password_page():
    return {
        "message": "Password reset link sent"
    }


app.include_router(auth_router)
app.include_router(biomarker_router)
app.include_router(alerts_router)
app.include_router(devices_router)
app.include_router(provider_router)
app.include_router(reports_router)
app.include_router(weather_router)  
app.include_router(withings_router)
app.include_router(users_router)
app.include_router(specialists_router)
app.include_router(apointments_router)
app.include_router(achievements_router) 
app.include_router(chat_router)
app.include_router(fitness_router)
app.include_router(dashboard_router)
