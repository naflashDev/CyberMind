"""
@file main.py
@brief Entry point for the Cyberintelligence FastAPI application.

@details This script initializes the UI of the Cebolla project using FastAPI.

@date Created: 2025-11-27 12:17:59
@author naflashDev
@project Cebolla
"""


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pathlib import Path
import uvicorn

app = FastAPI(title="UI Cebolla")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def home():
    return FileResponse(INDEX_FILE)


if __name__ == "__main__":
    # UI server configuration lives here
    uvicorn.run("ui_main:app", host="127.0.0.1", port=8080, reload=False)