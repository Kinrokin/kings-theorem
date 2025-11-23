"""
AID: /src/server.py
Proof ID: API-GATEWAY-001
Axiom: Integration

Purpose: Wraps the KT-v47 Engine in a FastAPI server.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import logging
from src.logging_config import setup_logging
from src.main import KTEngine

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

# Define the Output Model (What we send back)
class SolutionResponse(BaseModel):
    status: str
    kernel: str
    rationale: Optional[str] = None
    final_solution: Optional[Dict[str, Any]] = None
    teacher_artifact: Optional[Dict[str, Any]] = None

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
        
        return SolutionResponse(
            status=result.get("status", "UNKNOWN"),
            kernel=result.get("kernel", "UNKNOWN"),
            rationale=result.get("rationale"),
            final_solution=result.get("final_solution"),
            teacher_artifact=result.get("teacher_artifact") # This contains Qwen's answer
        )

    except Exception as e:
        logger.exception("Unhandled exception while solving request %s: %s", getattr(request, 'problem_id', 'N/A'), e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)