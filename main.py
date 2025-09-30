"""
SEO Audit System - Main FastAPI Application
Unified endpoint for Slack integration and SEO audit workflow
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes.slack_routes import router as slack_router
from services.seo_audit_orchestrator import SEOAuditOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting SEO Audit System...")
    
    # Check required environment variables
    required_env_vars = [
        'DATAFORSEO_USERNAME',
        'DATAFORSEO_PASSWORD', 
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET',
        'CLAUDE_API_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise Exception(f"Missing environment variables: {missing_vars}")
    
    logger.info("All required environment variables found")
    yield
    
    # Shutdown
    logger.info("Shutting down SEO Audit System...")

# Create FastAPI app
app = FastAPI(
    title="SEO Audit System",
    description="Automated SEO audit system with Slack integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(slack_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SEO Audit System API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "dataforseo": "configured" if os.getenv('DATAFORSEO_USERNAME') else "missing",
            "slack": "configured" if os.getenv('SLACK_BOT_TOKEN') else "missing",
            "claude": "configured" if os.getenv('CLAUDE_API_KEY') else "missing",
            "sheets": "configured" if os.getenv('GOOGLE_SHEETS_CREDENTIALS') else "missing"
        }
    }

@app.post("/api/seo-audit/direct")
async def run_direct_audit(domain: str, main_topic: str = None):
    """
    Direct API endpoint to run SEO audit without Slack
    Useful for testing and direct integration
    """
    try:
        logger.info(f"Starting direct SEO audit for {domain}")
        
        # Initialize orchestrator
        orchestrator = SEOAuditOrchestrator()
        
        # Run complete audit
        results = await orchestrator.run_complete_audit(domain, main_topic)
        
        if results.get('error'):
            raise HTTPException(status_code=500, detail=results['error'])
        
        return {
            "status": "success",
            "domain": domain,
            "results_file": results.get('results_file'),
            "summary": {
                "baseline_metrics": "completed",
                "competitor_analysis": "completed", 
                "content_opportunities": "completed",
                "keyword_prioritization": "completed",
                "serp_analysis": "completed"
            }
        }
        
    except Exception as e:
        logger.error(f"Direct audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
