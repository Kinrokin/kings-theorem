"""Test dashboard rendering with actual template."""
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()
PROJECT_ROOT = Path(__file__).parent

# Mount static files
STATIC_DIR = PROJECT_ROOT / "templates" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

@app.get("/", response_class=HTMLResponse)
async def test_dashboard(request: Request):
    """Render dashboard with test data."""
    context = {
        "request": request,
        "paused": False,
        "stopped": False,
        "level": 7,
        "epoch": 0,
        "best_metric": 0.0,
        "safety_violations": 0,
        "crash_counter": 0,
        "system_status": "Test Mode",
        "next_level": 8,
        "next_level_locked": False,
    }
    return templates.TemplateResponse("dashboard.html", context)

if __name__ == "__main__":
    print("🧪 Starting test dashboard on http://localhost:8085")
    uvicorn.run(app, host="127.0.0.1", port=8085, log_level="info", reload=False, workers=1)
