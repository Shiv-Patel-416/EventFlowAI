"""EventFlow AI — FastAPI Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, events, predictions, resources, diversions, feedback, analytics, dashboard

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Event-Driven Traffic Orchestration Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(resources.router, prefix="/api/resources", tags=["Resources"])
app.include_router(diversions.router, prefix="/api/diversions", tags=["Diversions"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
