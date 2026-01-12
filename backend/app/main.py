"""
TechTrainingPro - FastAPI Application Entry Point
Modern full-stack application with AI and DevOps capabilities
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import ai, devops, vision, location, storage


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events"""
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    print(f"📍 Environment: {settings.app_env}")
    print(f"🌐 Frontend URL: {settings.frontend_url}")
    yield
    # Shutdown
    print(f"👋 {settings.app_name} shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="""
    ## TechTrainingPro API
    
    A modern full-stack application featuring:
    - 🤖 **AI Chat** - Powered by Google Gemini 2.0
    - 🖼️ **Vision Analysis** - Multimodal image understanding
    - 🛠️ **Smart DevOps Agent** - AI-powered cloud management
    - 📍 **Location Services** - Geolocation features
    - 📦 **Cloud Storage** - S3 file operations
    
    Built with FastAPI + Next.js + Gemini AI
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(ai.router, prefix="/api/ai", tags=["AI & Chat"])
app.include_router(devops.router, prefix="/api/devops", tags=["DevOps Agent"])
app.include_router(vision.router, prefix="/api/vision", tags=["Vision Analysis"])
app.include_router(location.router, prefix="/api/location", tags=["Location Services"])
app.include_router(storage.router, prefix="/api/storage", tags=["Cloud Storage"])


@app.get("/", tags=["Health"])
async def root():
    """API root endpoint with basic info"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "features": [
            "AI Chat with Gemini 2.0",
            "Vision Analysis",
            "Smart DevOps Agent",
            "Location Services",
            "Cloud Storage (S3)"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "services": {
            "gemini": "configured" if settings.gemini_api_key else "not configured",
            "aws": "configured" if settings.aws_access_key_id else "not configured",
            "vision": "configured" if settings.google_vision_api_key else "using gemini"
        }
    }
