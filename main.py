import os
import sys
from dotenv import load_dotenv
import uvicorn

# Load .env file so GEMINI_API_KEY and other config are available
load_dotenv()

def run_server():
    """Starts the FastAPI server (supports cloud deployment host/port env variables)."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    environment = os.getenv("ENVIRONMENT", "development")
    # Disable reload in production environment
    reload = environment == "development"
    
    print("----------------------------------------------------------------")
    print("    ContextForge Core Context Optimization Engine Server        ")
    print(f"    Environment: {environment}                                  ")
    print(f"    Running on: http://{host}:{port}                           ")
    print(f"    API documentation: http://{host}:{port}/docs               ")
    print("----------------------------------------------------------------")
    uvicorn.run("contextforge.api.app:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        run_server()
    else:
        print("ContextForge Core Engine CLI")
        print("Usage: python main.py web   # Runs FastAPI REST Service")
