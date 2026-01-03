"""
FastAPI server for AFCON Chatbot
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.chatbot import AFCONChatbot, ResponseFormatter
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="AFCON Chatbot API",
    description="AI-powered chatbot for African Cup of Nations with live updates and historical insights",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot instance
chatbot: Optional[AFCONChatbot] = None


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    include_sources: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    type: str
    metadata: Dict[str, Any]
    success: bool
    sources: Optional[List[Dict]] = None


class SetLiveMatchRequest(BaseModel):
    """Request to set live match"""
    event_id: str


class MatchSummaryRequest(BaseModel):
    """Request for match summary"""
    event_id: str


# Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize chatbot on startup"""
    global chatbot
    try:
        chatbot = AFCONChatbot(use_conversational=True)
        print("✓ Chatbot initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing chatbot: {e}")
        chatbot = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AFCON Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy" if chatbot else "error"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if chatbot else "unhealthy",
        "chatbot_initialized": chatbot is not None
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics
    
    Returns:
        Cache statistics including entries, hits, and configuration
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        stats = chatbot.get_cache_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")


@app.post("/cache/clear")
async def clear_cache():
    """
    Clear response cache
    
    Returns:
        Confirmation message
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        chatbot.clear_cache()
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat query
    
    Args:
        request: Chat request with query
        
    Returns:
        Chat response with answer
    """
    if not chatbot:
        raise HTTPException(
            status_code=503, 
            detail="Chatbot not initialized. Check server logs."
        )
    
    try:
        # Get response from chatbot
        response = chatbot.chat(request.query)
        
        # Format for API
        formatted = ResponseFormatter.format_for_api(response)
        
        # Add sources if requested
        if request.include_sources and response.get("sources"):
            formatted["sources"] = [
                {
                    "content": doc.page_content if hasattr(doc, 'page_content') else str(doc),
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
                for doc in response["sources"][:5]  # Limit to 5 sources
            ]
        
        return formatted
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/live/set")
async def set_live_match(request: SetLiveMatchRequest):
    """
    Set the live match to monitor
    
    Args:
        request: Request with event ID
        
    Returns:
        Confirmation message
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        chatbot.set_live_match(request.event_id)
        return {
            "success": True,
            "message": f"Now monitoring match: {request.event_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting live match: {str(e)}")


@app.post("/match/summary")
async def get_match_summary(request: MatchSummaryRequest):
    """
    Get comprehensive match summary
    
    Args:
        request: Request with event ID
        
    Returns:
        Match summary data
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        summary = chatbot.get_match_summary(request.event_id)
        
        if "error" in summary:
            raise HTTPException(status_code=404, detail=summary["error"])
        
        return {
            "success": True,
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")


@app.post("/conversation/clear")
async def clear_conversation():
    """
    Clear conversation history
    
    Returns:
        Confirmation message
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    try:
        result = chatbot.clear_conversation()
        return {
            "success": True,
            "message": result["message"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


@app.get("/info")
async def get_info():
    """
    Get API information and configuration
    
    Returns:
        API info and settings
    """
    return {
        "api_version": "1.0.0",
        "llm_model": settings.groq_model,
        "embedding_model": settings.embedding_model,
        "vector_store_type": settings.vector_store_type,
        "features": {
            "live_updates": True,
            "historical_queries": True,
            "rag_enabled": True,
            "conversational": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AFCON Chatbot API Server...")
    print(f"📍 Server will be available at: http://{settings.host}:{settings.port}")
    print()
    
    uvicorn.run(
        "src.api.server:app",
        host=settings.host,
        port=settings.port,
        reload=False  # Disable reload to avoid issues
    )
