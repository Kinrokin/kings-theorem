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

class ApprovalRequest(BaseModel):
    token: str
    signature: str
    rationale: str

@app.get('/', response_class=HTMLResponse)
def ui_root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

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
