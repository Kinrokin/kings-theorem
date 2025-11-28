import logging
import os
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .utils import metrics as metrics_mod
from .utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(256, gt=0, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    output: str
    token_count: int


app = FastAPI(
    title="Kings Theorem Inference API",
    version="v1.0.0",
    description="Stateless and secure API serving the King's Theorem LLM.",
)


def get_api_token():
    """Return configured API token from environment, or None."""
    return os.getenv("KT_API_TOKEN")


def verify_auth(request: Request, api_token: str = Depends(get_api_token)):
    """Dependency that enforces token-based auth only if token is configured.

    Accepts Authorization: Bearer <token> or x-api-key header.
    """
    if not api_token:
        return True
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1].strip()
        if token == api_token:
            return True
    key = request.headers.get("x-api-key")
    if key and key == api_token:
        return True
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def add_metrics_and_logging(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.time() - start
        path = request.url.path
        metrics_mod.increment("requests_total")
        metrics_mod.observe_latency(path, duration)
        logger.info(
            "request path=%s status=%s duration=%.3f",
            path,
            getattr(response, "status_code", "N/A"),
            duration,
        )


@app.post("/v1/generate", response_model=GenerateResponse, dependencies=[Depends(verify_auth)])
async def generate(req: GenerateRequest):
    """Handles secure and validated inference requests."""
    logger.info("Received generate request, prompt_length=%d", len(req.prompt))

    # Input validation: enforce prompt length
    if len(req.prompt) > 5000:
        metrics_mod.increment("requests_rejected_long_prompt")
        raise HTTPException(status_code=400, detail="Prompt too long. Max 5000 characters.")

    # Mock inference (replace with real model invocation / sandbox)
    try:
        out = f"KT Proof generated for: '{req.prompt[:50]}...'"
        token_count = len(out.split()) + len(req.prompt.split())
        metrics_mod.increment("requests_success")
        return GenerateResponse(output=out, token_count=token_count)
    except Exception:
        logger.exception("Inference failed")
        metrics_mod.increment("requests_failed")
        raise HTTPException(status_code=500, detail="Model inference failed.")


@app.get("/metrics")
def metrics():
    data = metrics_mod.export_metrics()
    return PlainTextResponse(data, media_type="text/plain")
