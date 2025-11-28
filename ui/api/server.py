#!/usr/bin/env python3
"""
Ouroboros Tribunal API - The Visual Nexus
FastAPI server providing real-time metrics and dashboard for the Ouroboros Protocol.

Endpoints:
- /api/tribunal_report - Contamination and quality metrics
- /api/optimization_signal - Latest Ouroboros reward and config
- /api/curvature_metrics - Curved vs Euclidean distribution
- /dashboard - Interactive web dashboard
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

REPO_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PURIFIED_DIR = DATA_DIR / "purified"
EXPERIMENTS_DIR = DATA_DIR / "experiments"
HARVEST_DIR = DATA_DIR / "harvests"  # Legacy path
METRICS_DIR = DATA_DIR / "metrics"  # Legacy path
OUROBOROS_LOG = EXPERIMENTS_DIR / "experiment_log.jsonl"

app = FastAPI(
    title="Ouroboros Tribunal API",
    description="Real-time metrics and dashboard for the Ouroboros Protocol",
    version="2.0.0",
)


# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════


class SampleMetadata(BaseModel):
    """Metadata for a single sample in the browser list."""
    id: str
    short_id: str
    domain: str
    source: str
    final_score: float
    contamination_level: int


class SampleDetail(BaseModel):
    """Full sample details for modal view."""
    id: str
    short_id: str
    domain: str
    source: str
    instruction: str
    response_verbose: str
    response_compressed: str
    final_score: float
    compression_ratio: float
    new_token_count: int
    drift_score: float
    contamination_level: int


class TribunalSummary(BaseModel):
    """Summary metrics from a harvest."""
    harvest_path: str
    contamination_rate: float
    avg_final_score: float
    num_samples: int
    compression_ratio_avg: float
    contamination_buckets: List[int]
    sample_list: List[SampleMetadata]


class OptimizationSignal(BaseModel):
    """Latest Ouroboros optimization state."""
    iteration: int
    reward: float
    temperature: float
    curvature_ratio: float
    contamination_rate: float
    compression_density: float
    fractal_score_gain: float


class CurvatureMetrics(BaseModel):
    """Curvature distribution statistics."""
    total_samples: int
    euclidean_count: int
    curved_count: int
    curved_breakdown: Dict[str, int]
    curvature_preservation_rate: float


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def _safe_json_lines(path: Path) -> List[Dict[str, Any]]:
    """Safely load JSONL file, skipping malformed lines."""
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _latest_harvest() -> Optional[Path]:
    """Get path to most recent harvest file."""
    if not HARVEST_DIR.exists():
        return None
    candidates = sorted(HARVEST_DIR.glob("*.jsonl"))
    return candidates[-1] if candidates else None


def _latest_ouroboros_record() -> Optional[Dict[str, Any]]:
    """Get last Ouroboros iteration record."""
    if not OUROBOROS_LOG.exists():
        return None
    last_line = None
    with OUROBOROS_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last_line = line
    if not last_line:
        return None
    try:
        return json.loads(last_line)
    except json.JSONDecodeError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════


@app.get("/api/tribunal_report", response_model=TribunalSummary)
def get_tribunal_report(harvest: Optional[str] = None) -> TribunalSummary:
    """
    Get Tribunal summary for a specific harvest or the latest one.
    
    Provides contamination rate, average scores, and compression metrics.
    """
    if harvest:
        path = Path(harvest)
    else:
        path = _latest_harvest()

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="No harvest found")

    rows = _safe_json_lines(path)
    if not rows:
        raise HTTPException(status_code=400, detail="Harvest file is empty or invalid")

    n = len(rows)
    invalid = 0
    score_sum = 0.0
    compression_ratios: List[float] = []
    contamination_buckets: List[int] = []

    for row in rows:
        score = float(row.get("final_score", 0.0))
        verbose = str(row.get("response_verbose", "") or "")
        compressed = str(row.get("response_compressed", "") or "")
        
        # Determine severity level for heatmap
        # Level 0: Clean (score >= 0.95)
        # Level 1: Medium risk (0.85 <= score < 0.95)
        # Level 2+: High contamination (score < 0.85)
        if score >= 0.95 and verbose:
            severity = 0
        elif score >= 0.85:
            severity = 1
        else:
            severity = 2
        
        contamination_buckets.append(severity)
        
        if score < 0.90 or not verbose:
            invalid += 1
        
        score_sum += score
        
        if verbose and compressed:
            v_len = max(len(verbose), 1)
            c_len = len(compressed)
            compression_ratios.append(c_len / v_len)

    # Ensure exactly 100 buckets for 10x10 grid
    if len(contamination_buckets) < 100:
        contamination_buckets.extend([0] * (100 - len(contamination_buckets)))
    else:
        contamination_buckets = contamination_buckets[:100]

    contamination = invalid / n if n else 1.0
    avg_score = score_sum / n if n else 0.0
    avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0.0

    # Build sample list with metadata (up to 50 samples)
    import random
    sample_subset = random.sample(rows, min(50, n))
    sample_list = [
        SampleMetadata(
            id=str(s.get("id", "")),
            short_id=str(s.get("id", ""))[:8],
            domain=str(s.get("domain", "")),
            source=str(s.get("source", "")),
            final_score=float(s.get("final_score", 0.0)),
            contamination_level=int(s.get("contamination_level", 0)),
        )
        for s in sample_subset
    ]

    return TribunalSummary(
        harvest_path=str(path),
        contamination_rate=contamination,
        avg_final_score=avg_score,
        num_samples=n,
        compression_ratio_avg=avg_compression,
        contamination_buckets=contamination_buckets,
        sample_list=sample_list,
    )


@app.get("/api/tribunal_sample")
def get_tribunal_sample(id: str, harvest: Optional[str] = None) -> Dict[str, Any]:
    """
    Get full details for a specific sample by ID.
    
    Returns complete sample data for modal view.
    """
    if harvest:
        path = Path(harvest)
    else:
        path = _latest_harvest()

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="No harvest found")

    rows = _safe_json_lines(path)
    
    # Find sample by ID
    for row in rows:
        if str(row.get("id", "")) == id:
            return {
                "id": str(row.get("id", "")),
                "short_id": str(row.get("id", ""))[:8],
                "domain": str(row.get("domain", "")),
                "source": str(row.get("source", "")),
                "instruction": str(row.get("instruction", "")),
                "response_verbose": str(row.get("response_verbose", "")),
                "response_compressed": str(row.get("response_compressed", "")),
                "final_score": float(row.get("final_score", 0.0)),
                "compression_ratio": float(row.get("compression_ratio", 0.0)),
                "new_token_count": int(row.get("new_token_count", 0)),
                "drift_score": float(row.get("drift_score", 0.0)),
                "contamination_level": int(row.get("contamination_level", 0)),
            }
    
    raise HTTPException(status_code=404, detail=f"Sample {id} not found")


@app.get("/api/optimization_signal", response_model=OptimizationSignal)
def get_optimization_signal() -> OptimizationSignal:
    """
    Get latest Ouroboros optimization state.
    
    Returns current reward, temperature, and curvature ratio.
    """
    record = _latest_ouroboros_record()
    if record is None:
        raise HTTPException(status_code=404, detail="No Ouroboros log found")

    return OptimizationSignal(
        iteration=int(record.get("iteration", 0)),
        reward=float(record.get("reward", 0.0)),
        temperature=float(record.get("temperature", 0.0)),
        curvature_ratio=float(record.get("curvature_ratio", 0.0)),
        contamination_rate=float(record.get("contamination_rate", 0.0)),
        compression_density=float(record.get("compression_density", 0.0)),
        fractal_score_gain=float(record.get("fractal_score_gain", 0.0)),
    )


@app.get("/api/curvature_metrics", response_model=CurvatureMetrics)
def get_curvature_metrics(harvest: Optional[str] = None) -> CurvatureMetrics:
    """
    Get curvature distribution statistics.
    
    Shows breakdown of Euclidean vs Curved samples and preservation rates.
    """
    if harvest:
        path = Path(harvest)
    else:
        path = _latest_harvest()

    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="No harvest found")

    rows = _safe_json_lines(path)
    total = len(rows)
    if total == 0:
        raise HTTPException(status_code=400, detail="Harvest file is empty or invalid")

    euclidean = 0
    curved = 0
    breakdown: Dict[str, int] = {}
    preserved = 0

    for row in rows:
        source = str(row.get("source", "")).upper()
        curvature_preserved = row.get("curvature_preserved", False)
        
        if "EUCLIDEAN" in source:
            euclidean += 1
        elif "CURVED" in source or "FUSION" in source:
            curved += 1
            
            # Extract curvature type
            if "HYPERBOLIC" in source:
                key = "HYPERBOLIC"
            elif "ELLIPTIC" in source:
                key = "ELLIPTIC"
            elif "PARABOLIC" in source:
                key = "PARABOLIC"
            elif "RETROCAUSAL" in source:
                key = "RETROCAUSAL"
            elif "FUSION" in source:
                key = "FUSION"
            else:
                key = "OTHER_CURVED"
                
            breakdown[key] = breakdown.get(key, 0) + 1
            
            if curvature_preserved:
                preserved += 1

    preservation_rate = preserved / curved if curved > 0 else 0.0

    return CurvatureMetrics(
        total_samples=total,
        euclidean_count=euclidean,
        curved_count=curved,
        curved_breakdown=breakdown,
        curvature_preservation_rate=preservation_rate,
    )


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    """
    Interactive dashboard for Ouroboros monitoring.
    
    Displays:
    - Tribunal contamination metrics
    - Optimization reward trajectory
    - Curvature distribution and preservation
    - Real-time auto-refresh
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🐍 Ouroboros Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
                background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
                color: #e0e7ff;
                padding: 2rem;
                line-height: 1.6;
            }
            
            .header {
                text-align: center;
                margin-bottom: 2rem;
                padding: 1.5rem;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            h1 {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .subtitle {
                font-size: 0.9rem;
                opacity: 0.7;
                letter-spacing: 0.05em;
            }
            
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }
            
            .card {
                background: rgba(255, 255, 255, 0.04);
                padding: 1.5rem;
                border-radius: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 25px 70px rgba(0, 0, 0, 0.6);
            }
            
            h2 {
                font-size: 1.3rem;
                margin-bottom: 1rem;
                color: #818cf8;
                border-bottom: 2px solid rgba(129, 140, 248, 0.3);
                padding-bottom: 0.5rem;
            }
            
            pre {
                background: rgba(0, 0, 0, 0.3);
                padding: 1rem;
                border-radius: 0.5rem;
                overflow-x: auto;
                font-size: 0.85rem;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            
            .metric {
                display: flex;
                justify-content: space-between;
                padding: 0.75rem;
                margin: 0.5rem 0;
                background: rgba(129, 140, 248, 0.1);
                border-radius: 0.5rem;
                border-left: 3px solid #818cf8;
            }
            
            .metric-label {
                opacity: 0.8;
                font-weight: 500;
            }
            
            .metric-value {
                font-weight: bold;
                color: #c084fc;
            }
            
            .status {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 1rem;
                font-size: 0.75rem;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .status-good { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
            .status-warn { background: rgba(251, 146, 60, 0.2); color: #fb923c; }
            .status-bad { background: rgba(239, 68, 68, 0.2); color: #f87171; }
            
            .loading {
                text-align: center;
                opacity: 0.6;
                font-style: italic;
            }
            
            .error {
                color: #f87171;
                background: rgba(239, 68, 68, 0.1);
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 3px solid #f87171;
            }
            
            .timestamp {
                text-align: center;
                margin-top: 2rem;
                opacity: 0.5;
                font-size: 0.85rem;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐍 Ouroboros Dashboard</h1>
            <div class="subtitle">THE VISUAL NEXUS - REAL-TIME PROTOCOL MONITORING</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>⚖️ Tribunal Summary</h2>
                <div id="tribunal" class="loading">Initializing...</div>
            </div>
            
            <div class="card">
                <h2>🎯 Optimization Signal</h2>
                <div id="opt" class="loading">Initializing...</div>
            </div>
            
            <div class="card">
                <h2>🌀 Curvature Metrics</h2>
                <div id="curvature" class="loading">Initializing...</div>
            </div>
        </div>

        <div class="timestamp" id="timestamp"></div>

        <script>
        function getStatusClass(value, metric) {
            if (metric === 'contamination') {
                if (value < 0.05) return 'status-good';
                if (value < 0.15) return 'status-warn';
                return 'status-bad';
            }
            if (metric === 'reward') {
                if (value >= 0.80) return 'status-good';
                if (value >= 0.60) return 'status-warn';
                return 'status-bad';
            }
            if (metric === 'preservation') {
                if (value >= 0.80) return 'status-good';
                if (value >= 0.50) return 'status-warn';
                return 'status-bad';
            }
            return 'status-good';
        }

        function formatMetric(label, value, unit = '', metric = null) {
            const statusClass = metric ? getStatusClass(value, metric) : '';
            const statusHTML = metric ? `<span class="status ${statusClass}">${value.toFixed(3)}</span>` : value.toFixed(3);
            return `<div class="metric">
                <span class="metric-label">${label}</span>
                <span class="metric-value">${statusHTML}${unit}</span>
            </div>`;
        }

        async function loadTribunal() {
            const el = document.getElementById('tribunal');
            try {
                const resp = await fetch('/api/tribunal_report');
                if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
                
                const data = await resp.json();
                
                el.innerHTML = `
                    ${formatMetric('Contamination Rate', data.contamination_rate, '', 'contamination')}
                    ${formatMetric('Avg Final Score', data.avg_final_score)}
                    ${formatMetric('Compression Ratio', data.compression_ratio_avg)}
                    ${formatMetric('Total Samples', data.num_samples, '')}
                    <pre style="margin-top: 1rem; font-size: 0.75rem; opacity: 0.7;">Harvest: ${data.harvest_path.split('/').pop()}</pre>
                `;
            } catch (err) {
                el.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        }

        async function loadOptimization() {
            const el = document.getElementById('opt');
            try {
                const resp = await fetch('/api/optimization_signal');
                if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
                
                const data = await resp.json();
                
                el.innerHTML = `
                    ${formatMetric('Composite Reward', data.reward, '', 'reward')}
                    ${formatMetric('Temperature', data.temperature)}
                    ${formatMetric('Curvature Ratio', data.curvature_ratio)}
                    ${formatMetric('Fractal Score Gain', data.fractal_score_gain)}
                    <pre style="margin-top: 1rem; font-size: 0.75rem; opacity: 0.7;">Iteration: ${data.iteration}</pre>
                `;
            } catch (err) {
                el.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        }

        async function loadCurvature() {
            const el = document.getElementById('curvature');
            try {
                const resp = await fetch('/api/curvature_metrics');
                if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
                
                const data = await resp.json();
                
                const breakdownHTML = Object.entries(data.curved_breakdown)
                    .map(([k, v]) => `<div style="padding: 0.25rem 0;">${k}: ${v}</div>`)
                    .join('');
                
                el.innerHTML = `
                    ${formatMetric('Total Samples', data.total_samples, '')}
                    ${formatMetric('Euclidean', data.euclidean_count, '')}
                    ${formatMetric('Curved', data.curved_count, '')}
                    ${formatMetric('Preservation Rate', data.curvature_preservation_rate, '', 'preservation')}
                    <pre style="margin-top: 1rem; font-size: 0.75rem;">${breakdownHTML || 'No curved samples yet'}</pre>
                `;
            } catch (err) {
                el.innerHTML = `<div class="error">❌ ${err.message}</div>`;
            }
        }

        function updateTimestamp() {
            document.getElementById('timestamp').textContent = 
                `Last updated: ${new Date().toLocaleString()}`;
        }

        function refreshAll() {
            loadTribunal();
            loadOptimization();
            loadCurvature();
            updateTimestamp();
        }

        // Initial load
        refreshAll();
        
        // Auto-refresh every 10 seconds
        setInterval(refreshAll, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/api/qwen_status")
def get_qwen_status() -> Dict[str, Any]:
    """
    Get Qwen backend health status.
    
    Returns backend type, availability, and configuration.
    """
    try:
        from src.llm.router import get_backend_status
        return get_backend_status()
    except Exception as e:
        return {
            "backend": "unknown",
            "ok": False,
            "error": f"Failed to get backend status: {e}",
            "config": {}
        }


@app.websocket("/ws/metrics")
async def ws_metrics(ws: WebSocket) -> None:
    """
    WebSocket endpoint for live metrics streaming.
    
    Streams combined metrics every 5 seconds:
    - Tribunal summary
    - Optimization signal  
    - Curvature metrics
    """
    await ws.accept()
    try:
        import asyncio
        while True:
            # Gather all metrics
            try:
                tribunal = get_tribunal_report()
                tribunal_dict = tribunal.model_dump()
            except Exception:
                tribunal_dict = None
            
            try:
                opt = get_optimization_signal()
                opt_dict = opt.model_dump()
            except Exception:
                opt_dict = None
            
            try:
                curv = get_curvature_metrics()
                curv_dict = curv.model_dump()
            except Exception:
                curv_dict = None

            # Send combined payload
            payload = {
                "tribunal": tribunal_dict,
                "optimization": opt_dict,
                "curvature": curv_dict,
            }
            await ws.send_text(json.dumps(payload, ensure_ascii=False))
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5.0)
            
    except WebSocketDisconnect:
        # Client disconnected, clean up
        return


if __name__ == "__main__":
    import uvicorn
    print("🐍 Starting Ouroboros Tribunal API Server...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🔌 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
