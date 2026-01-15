"""
OmniDev - FastAPI Application Entry Point
Modern full-stack application with AI and DevOps capabilities
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import ai, devops, vision, location, storage, scraper


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
    ## OmniDev API
    
    An all-in-one AI-powered developer platform featuring:
    - 🤖 **AI Chat** - Powered by OpenAI GPT-5 Mini
    - 🖼️ **Vision Analysis** - Multimodal image understanding with GPT-5 Mini Vision
    - 🛠️ **Smart DevOps Agent** - AI-powered cloud management
    - 🕷️ **Web Scraper** - Playwright browser automation
    - 📍 **Location Services** - Geolocation features
    - 📦 **Cloud Storage** - S3 file operations
    
    Built with FastAPI + Next.js + OpenAI GPT-5 Mini
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
app.include_router(scraper.router, prefix="/api/scraper", tags=["Web Scraper"])
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
            "AI Chat with OpenAI GPT-5 Mini",
            "Vision Analysis with GPT-5 Mini",
            "Smart DevOps Agent",
            "Web Scraper (Playwright)",
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
            "openai": "configured" if settings.openai_api_key else "not configured",
            "aws": "configured" if settings.aws_access_key_id else "not configured",
            "scraper": "available"
        }
    }
