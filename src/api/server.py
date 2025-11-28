import os
import yaml
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
from src.ledger.integrity_ledger import IntegrityLedger, LedgerError
from src.runtime.council_router import CouncilRouter

def load_config():
    base = Path(__file__).resolve().parent.parent.parent
    cfg = base / 'config' / 'master_config.yaml'
    if cfg.exists():
        with open(cfg, 'r') as f: return yaml.safe_load(f)
    return {}

conf = load_config()
API_KEY = os.getenv(conf.get('security', {}).get('api_key_env', 'KT_API_KEY'), 'kthitl_dev')

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title='KT-v53.6 Sovereign Interface')
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory=str(os.path.join(os.path.dirname(__file__), 'templates')))
app.mount('/static', StaticFiles(directory=str(os.path.join(os.path.dirname(__file__), 'static'))), name='static')

ledger = IntegrityLedger(conf=conf)

# Initialize Council Router for Sovereign Interface
try:
    council = CouncilRouter()
except Exception as e:
    print(f"Warning: Council Router not available: {e}")
    council = None

class ApprovalRequest(BaseModel):
    token: str
    signature: str
    rationale: str

class SovereignWarrant(BaseModel):
    warrant: str
    mode: str = "DEAN"

@app.get('/', response_class=HTMLResponse)
def ui_root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get('/sovereign', response_class=HTMLResponse)
def sovereign_interface(request: Request):
    """Sovereign Interface v2.0 - Constitutional Cockpit"""
    return templates.TemplateResponse('sovereign.html', {'request': request})

@app.post('/approve')
@limiter.limit('5/minute')
def approve_proposal(req: ApprovalRequest, request: Request, x_api_key: str = Header(None)):
    if x_api_key!= API_KEY:
        raise HTTPException(401, 'Unauthorized')
    if len(req.rationale.strip()) < 10:
        raise HTTPException(400, 'Rationale too short')

    try:
        tx_hash = ledger.finalize_proposal(req.token, req.signature, req.rationale, kid='operator.pub')
        # Platinum: Auto-trigger block seal check for demo purposes
        ledger.seal_block(batch_size=5)
        return {'status': 'COMMITTED', 'tx_hash': tx_hash}
    except LedgerError as e:
        code_map = {'INVALID_TOKEN':404, 'TOKEN_EXPIRED':408, 'INVALID_SIGNATURE':403, 'CHAIN_DIVERGENCE':409}
        return JSONResponse(status_code=code_map.get(e.code, 500), content={'error': e.code, 'message': str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': 'INTERNAL_ERROR', 'message': str(e)})

@app.post('/api/sovereign/decree')
@limiter.limit('30/minute')
async def sovereign_decree(req: SovereignWarrant, request: Request, x_api_key: str = Header(None)):
    """
    Sovereign Interface Endpoint
    
    Issues warrants to the Council and returns decrees.
    This is the constitutional backend for the Sovereign Cockpit.
    """
    # Optional: API key check (can be disabled for local use)
    # if x_api_key != API_KEY:
    #     raise HTTPException(401, 'Unauthorized')
    
    if not council:
        raise HTTPException(503, 'Council Router not available')
    
    if not req.warrant or len(req.warrant.strip()) < 3:
        raise HTTPException(400, 'Warrant too short')
    
    # Validate mode
    valid_modes = ['DEAN', 'ENGINEER', 'ARBITER', 'TA']
    if req.mode not in valid_modes:
        raise HTTPException(400, f'Invalid mode. Must be one of: {valid_modes}')
    
    try:
        # Route warrant to Council
        response = council.route_request(
            role=req.mode,
            prompt=req.warrant,
            system_msg=f"You are operating in {req.mode} mode for King's Theorem Sovereign Interface.",
            max_tokens=2048
        )
        
        # Check for constitutional violations (simple heuristic)
        # In production, integrate with actual governance layer
        veto_keywords = ['hack', 'exploit', 'bypass', 'jailbreak']
        if any(keyword in req.warrant.lower() for keyword in veto_keywords):
            return JSONResponse(
                status_code=200,
                content={
                    'status': 'VETO',
                    'veto': True,
                    'message': 'Constitutional violation: Attempted bypass of safety protocols'
                }
            )
        
        return {
            'status': 'DECREE',
            'decree': response,
            'response': response,
            'mode': req.mode,
            'veto': False
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'status': 'ERROR',
                'error': 'COUNCIL_ERROR',
                'message': str(e)
            }
        )
