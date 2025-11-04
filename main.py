from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config

# Validate configuration on startup
Config.validate()

app = FastAPI(
    title="Memoir Generator MVP",
    description="Backend API for generating technical memoirs using RAG",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === HEALTH CHECK ===

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {
        "status": "ok",
        "service": "memoir-generator-backend",
        "version": "0.1.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Memoir Generator API",
        "docs": "/docs",
        "health": "/health"
    }

# === STARTUP EVENT ===

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Memoir Generator API starting...")
    print(f"📍 Supabase URL: {Config.SUPABASE_URL}")
    print(f"🔑 Claude API Key configured: {'Yes' if Config.CLAUDE_API_KEY else 'No'}")
    print(f"🔑 OpenAI API Key configured: {'Yes' if Config.OPENAI_API_KEY else 'No'}")
    print("✅ Configuration validated successfully")

    # Test Supabase connection
    try:
        from services.supabase import get_supabase
        supabase = get_supabase()
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
