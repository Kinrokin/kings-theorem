"""FastAPI Server Wrapper for Canonical KTEngine (Phoenix Phase 4)."""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure project root on path before importing src.* modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from src.core.kt_engine import KTEngine  # noqa: E402
from src.logging_config import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)

# Initialize the App and the Engine
app = FastAPI(title="King's Theorem (KT-v47) API", version="1.0")
engine = KTEngine()


# Define the Input Model (What the user sends)
class ProblemRequest(BaseModel):
    problem_id: str
    # We use Dict[str, Any] because the problem structure is dynamic (graphs, logic, etc.)
    problem_graph: Dict[str, Any]


class RiskSummary(BaseModel):
    aggregate: float
    tier: str
    components: Dict[str, float] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    phase: str
    name: str
    status: str
    meta: Dict[str, Any] = Field(default_factory=dict)


# Define the Output Model (What we send back)
class SolutionResponse(BaseModel):
    status: str
    kernel: str
    rationale: Optional[str] = None
    final_solution: Optional[Dict[str, Any]] = None
    teacher_artifact: Optional[Dict[str, Any]] = None
    risk: RiskSummary
    governance: Dict[str, Any] = Field(default_factory=dict)
    trace: List[TraceEvent] = Field(default_factory=list)


@app.get("/")
def read_root():
    return {"system": "KT-v47 Parallel Cognitive Kernel", "status": "ONLINE"}


@app.post("/solve", response_model=SolutionResponse)
def solve_problem(request: ProblemRequest):
    """
    The main endpoint. Receives a problem, runs the engine, returns the solution.
    """
    try:
        logger.info("[API] Received request: %s", request.problem_id)

        # Execute the engine
        # We merge the ID into the graph for the engine to use
        graph = request.problem_graph
        graph["problem_id"] = request.problem_id

        result = engine.execute(graph)

        raw_risk = result.get("risk") or {}
        components = raw_risk.get("components") or {}
        safe_components: Dict[str, float] = {}
        for key, value in components.items():
            try:
                safe_components[str(key)] = float(value)
            except (TypeError, ValueError):
                logger.warning("[API] Non-numeric risk component %s=%s", key, value)
                safe_components[str(key)] = 0.0

        risk_summary = RiskSummary(
            aggregate=float(raw_risk.get("aggregate", 0.0) or 0.0),
            tier=str(raw_risk.get("tier", "LOW")),
            components=safe_components,
        )

        raw_trace = result.get("trace") or []
        trace_events: List[TraceEvent] = []
        for event in raw_trace:
            meta = event.get("meta") if isinstance(event.get("meta"), dict) else {"detail": event.get("meta")}
            trace_events.append(
                TraceEvent(
                    phase=str(event.get("phase", "UNKNOWN")),
                    name=str(event.get("name", "UNKNOWN")),
                    status=str(event.get("status", "UNKNOWN")),
                    meta=meta,
                )
            )

        return SolutionResponse(
            status=result.get("status", "UNKNOWN"),
            kernel=result.get("kernel", "UNKNOWN"),
            rationale=result.get("rationale"),
            final_solution=result.get("final_solution"),
            teacher_artifact=result.get("teacher_artifact"),
            risk=risk_summary,
            governance=result.get("governance", {}),
            trace=trace_events,
        )

    except Exception as e:
        logger.exception(
            "Unhandled exception while solving request %s: %s",
            getattr(request, "problem_id", "N/A"),
            e,
        )
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server
    import uvicorn

    host = os.getenv("KT_BIND_HOST", "127.0.0.1")
    port = int(os.getenv("KT_BIND_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
