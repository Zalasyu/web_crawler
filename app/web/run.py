import uvicorn
from fastapi import FastAPI
import threading
from app.web.api import app as fastapi_app
from app.web.ui import demo

def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Start FastAPI in a background thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Run Gradio in the main thread
    demo.launch()