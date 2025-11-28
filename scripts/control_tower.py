#!/usr/bin/env python3
"""
Control Tower: Human Command Interface for King's Theorem Research Loop.

This FastAPI service provides a web UI for human operators to:
- PAUSE/RESUME the autonomous training loop
- Trigger EMERGENCY STOP (graceful shutdown)
- UNLOCK curriculum level promotions via governance gates
- CHAT with the Council of Teachers (DEAN/ENGINEER/ARBITER/TA)

Endpoints:
- GET /         : Dashboard with system status and control buttons
- POST /action  : Execute control commands (PAUSE/RESUME/STOP/UNLOCK)
- POST /api/chat: Direct interface to Council Router

Signal Files (shared via Docker volume):
- data/PAUSE        : Freeze loop until removed
- data/STOP         : Graceful shutdown with state save
- data/ALLOW_LEVEL_X: Unlock promotion to level X

Author: King's Theorem Team
License: MIT
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="King's Theorem Control Tower")

# Add project root to path for imports
SCRIPT_DIR_PATH = Path(__file__).parent.absolute()
PROJECT_ROOT_PATH = SCRIPT_DIR_PATH.parent
sys.path.insert(0, str(PROJECT_ROOT_PATH))

# Lazy-load Council Router (initialized on first use)
_council_router = None

def get_council():
    """Lazy initialization of Council Router."""
    global _council_router
    if _council_router is None:
        try:
            from src.runtime.council_router import CouncilRouter
            _council_router = CouncilRouter()
            logger.info("✅ Council Router initialized with 15-model roster")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Council Router: {e}")
            _council_router = None
    return _council_router

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent

# Docker mount point (overridden in docker-compose.yml)
DATA_DIR = Path("/app/data")
TEMPLATES_DIR = Path("/app/templates")

# Fallback for local dev
if not DATA_DIR.exists():
    DATA_DIR = PROJECT_ROOT / "data"
    logger.warning(f"Using local data directory: {DATA_DIR}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = PROJECT_ROOT / "templates"
    logger.warning(f"Using local templates directory: {TEMPLATES_DIR}")

# Mount static files (CSS/JS) under /static - MUST be before routes
STATIC_DIR = TEMPLATES_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Static directory: {STATIC_DIR}")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize templates AFTER static mount
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# --- SIGNAL FILE HELPERS ---


def set_signal(name: str) -> None:
    """Create a signal file to communicate with the research loop."""
    signal_file = DATA_DIR / name
    signal_file.touch()
    logger.info(f"🔔 Signal set: {name}")


def clear_signal(name: str) -> None:
    """Remove a signal file."""
    signal_file = DATA_DIR / name
    if signal_file.exists():
        signal_file.unlink()
        logger.info(f"🔕 Signal cleared: {name}")


def is_active(name: str) -> bool:
    """Check if a signal file exists."""
    return (DATA_DIR / name).exists()


def get_status() -> Dict[str, Any]:
    """Read the engine's current state from system_state.json."""
    state_file = DATA_DIR / "system_state.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                return {
                    "level": state.get("level", 1),
                    "epoch": state.get("epoch", 0),
                    "best_metric": state.get("best_metric", 0.0),
                    "safety_violations": state.get("safety_violations", 0),
                    "crash_counter": state.get("crash_counter", 0),
                    "status": "Running",
                }
        except json.JSONDecodeError:
            logger.error("Failed to parse system_state.json")
            return {"level": 0, "epoch": 0, "status": "Error: Corrupted state file"}
    else:
        return {"level": 0, "epoch": 0, "status": "Offline"}


# --- ROUTES ---


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the main control dashboard."""
    try:
        status = get_status()
        current_level = status.get("level", 1)

        context = {
            "request": request,
            "paused": is_active("PAUSE"),
            "stopped": is_active("STOP"),
            "level": current_level,
            "epoch": status.get("epoch", 0),
            "best_metric": status.get("best_metric", 0.0),
            "safety_violations": status.get("safety_violations", 0),
            "crash_counter": status.get("crash_counter", 0),
            "system_status": status.get("status", "Unknown"),
            "next_level": current_level + 1,
            "next_level_locked": not is_active(f"ALLOW_LEVEL_{current_level + 1}"),
        }

        return templates.TemplateResponse("dashboard.html", context)
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>", status_code=500)


@app.post("/action")
async def action(command: str = Form(...), level: int = Form(0)) -> RedirectResponse:
    """Execute control commands from the dashboard."""

    if command == "PAUSE":
        set_signal("PAUSE")
        logger.info("🛑 Loop PAUSED by operator")

    elif command == "RESUME":
        clear_signal("PAUSE")
        logger.info("▶️ Loop RESUMED by operator")

    elif command == "STOP":
        set_signal("STOP")
        logger.critical("🚨 EMERGENCY STOP triggered by operator")

    elif command == "UNLOCK":
        if level > 0:
            set_signal(f"ALLOW_LEVEL_{level}")
            logger.info(f"🔓 Level {level} UNLOCKED by operator")
        else:
            logger.error("Invalid level for UNLOCK command")

    else:
        logger.warning(f"Unknown command: {command}")

    return RedirectResponse(url="/", status_code=303)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for Docker."""
    return {"status": "healthy", "service": "control_tower"}


# --- CHAT API ---


class ChatRequest(BaseModel):
    """Chat request schema."""
    query: str
    mode: str = "architect"


@app.post("/api/chat")
async def api_chat(req: ChatRequest) -> Dict[str, Any]:
    """
    Direct interface to the Council of Teachers.
    
    Maps UI personas to Council specialist roles:
    - architect -> DEAN (Deep reasoning for design)
    - critic -> ARBITER (Rigorous evaluation)
    - ops -> TA (Quick operational queries)
    - crucible -> ENGINEER (Technical implementation)
    """
    council = get_council()
    
    if council is None:
        return {
            "answer": "❌ Council Router unavailable. Please check OPENROUTER_API_KEY is set.",
            "error": True,
            "governance": {
                "paradoxes_detected": 0,
                "safety_violations_prevented": 0
            }
        }
    
    try:
        # Map UI modes to Council Roles
        role_map = {
            "architect": "DEAN",      # Design & reasoning
            "critic": "ARBITER",      # Evaluation & grading
            "ops": "TA",              # Quick operational tasks
            "crucible": "ENGINEER"    # Technical implementation
        }
        council_role = role_map.get(req.mode, "TA")
        
        # System messages for each persona
        system_messages = {
            "architect": "You are the Architect persona for King's Theorem. You specialize in system design, reasoning architecture, and strategic planning. Provide clear, principled guidance.",
            "critic": "You are the Critic persona for King's Theorem. You rigorously evaluate proposals for safety, correctness, and ethical implications. Be thorough and uncompromising.",
            "ops": "You are the Ops persona for King's Theorem. You handle system operations, monitoring, and quick troubleshooting. Be concise and actionable.",
            "crucible": "You are the Crucible persona for King's Theorem. You design and implement technical solutions, write code, and handle complex engineering challenges."
        }
        
        system_msg = system_messages.get(req.mode, "You are a helpful AI assistant for the King's Theorem system.")
        
        # Execute Generation via Council
        logger.info(f"🔀 Chat request routed to {council_role} ({req.mode} persona)")
        answer = council.route_request(
            role=council_role,
            prompt=req.query,
            system_msg=system_msg,
            max_tokens=1500
        )
        
        return {
            "answer": answer,
            "governance": {
                "paradoxes_detected": 0,  # Placeholder for future governance integration
                "safety_violations_prevented": 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Council chat error: {e}", exc_info=True)
        return {
            "answer": f"❌ Council Error: {str(e)}",
            "error": True,
            "governance": {
                "paradoxes_detected": 0,
                "safety_violations_prevented": 0
            }
        }


# --- MAIN ENTRY POINT ---

if __name__ == "__main__":
    import uvicorn

    # Ensure templates directory exists
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("🏯 King's Theorem Control Tower starting...")
    logger.info(f"   Data directory: {DATA_DIR}")
    logger.info(f"   Templates: {TEMPLATES_DIR}")
    logger.info("   Dashboard available at: http://localhost:8080")

    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info", reload=False, workers=1)
