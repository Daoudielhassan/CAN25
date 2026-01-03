"""
Simple server startup script without automatic reload
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AFCON Chatbot API Server")
    print("=" * 60)
    print()
    print(f"📍 Server URL: http://{settings.host}:{settings.port}")
    print(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        uvicorn.run(
            "src.api.server:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
