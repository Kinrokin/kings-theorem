# 🚀 Ouroboros Protocol - Installation Guide

Complete setup instructions for the Ouroboros Protocol v2.0 full-stack system.

---

## 📋 Prerequisites

### Required Software
- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads))

### Optional
- **GPU** with CUDA (for faster local model inference)
- **VSCode** (recommended IDE)

---

## 🔧 Installation Steps

### 1. Clone Repository
```powershell
git clone https://github.com/Kinrokin/kings-theorem.git
cd kings-theorem
```

### 2. Python Environment Setup

#### Option A: Virtual Environment (Recommended)
```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Conda
```powershell
conda create -n ouroboros python=3.10
conda activate ouroboros
pip install -r requirements.txt
```

### 3. Frontend Setup
```powershell
cd ui\frontend
npm install
cd ..\..
```

### 4. Environment Configuration

Create `.env` file in repository root:

```env
# OpenAI API (for GPT-4o models)
OPENAI_API_KEY=sk-your-key-here

# Optional: Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key

# Optional: Local model endpoints
OLLAMA_BASE_URL=http://localhost:11434
```

### 5. Verify Installation

#### Backend Test
```powershell
python -c "from src.crucibles.reward import compute_reward; print('✅ Backend OK')"
```

#### Frontend Test
```powershell
cd ui\frontend
npm run build
cd ..\..
```

If both succeed, installation is complete!

---

## 🎯 Quick Start

### Minimal Test (No LLM Required)
```powershell
# Validate structure
python scripts\validate_ouroboros.py
```

**Expected output:**
```
Testing Ouroboros Protocol implementation...
✓ Import validation passed
✓ Event Horizon validation passed
✓ Domain curvature validation passed
✓ Fusion generator validation passed

ALL TESTS PASSED (6/6)
```

### Generate First Dataset
```powershell
# 10 samples, mixed Euclidean/Curved
python scripts\run_curved_curriculum.py --count 10 --curvature-ratio 0.50
```

**Output file:** `data/harvests/curriculum_TIMESTAMP.jsonl`

### Launch Dashboard
```powershell
# Automated full-stack launcher
.\ui\launch_dashboard.ps1
```

**Opens:** `http://localhost:5173`

---

## 🔌 Model Configuration

### Option 1: OpenAI API (Recommended)
```powershell
# Set API key
$env:OPENAI_API_KEY = "sk-your-key"

# Test
python -c "from openai import OpenAI; print(OpenAI().models.list().data[0].id)"
```

### Option 2: Azure OpenAI
```powershell
# Set Azure credentials
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_API_KEY = "your-key"

# Update CouncilRouter config in scripts
# (See config/master_config.yaml)
```

### Option 3: Local Models (Ollama)
```powershell
# Install Ollama: https://ollama.ai

# Pull models
ollama pull llama3.1:70b
ollama pull phi3

# Set base URL
$env:OLLAMA_BASE_URL = "http://localhost:11434"

# Update CouncilRouter to use local endpoints
```

---

## 📦 Dependency Details

### Python Packages (requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0
```

### Frontend Packages (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.10.0",
    "clsx": "^2.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.4.1",
    "vite": "^5.0.5"
  }
}
```

---

## 🛠️ Configuration Files

### Backend (Python)
**File:** `config/master_config.yaml`

```yaml
council:
  router_type: "model-based"
  models:
    DEAN:
      model: "gpt-4o"
      temperature: 1.1
    ARBITER:
      model: "gpt-4o-mini"
      temperature: 0.3
    NEMOTRON:
      model: "llama-3.1-70b-instruct"
      temperature: 0.7
```

### Frontend (React)
**File:** `ui/frontend/vite.config.js`

```js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
});
```

---

## 🚨 Troubleshooting

### Issue: `python` command not found
**Windows:**
```powershell
# Use py launcher
py -m pip install -r requirements.txt
py scripts\run_curved_curriculum.py
```

**Fix permanently:**
1. Open "Edit system environment variables"
2. Add Python install directory to PATH
3. Restart terminal

### Issue: `npm install` fails with `EACCES` error
**Fix:**
```powershell
# Use administrator PowerShell
Start-Process powershell -Verb runAs
cd ui\frontend
npm install
```

### Issue: `ModuleNotFoundError: No module named 'fastapi'`
**Fix:**
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn
```

### Issue: Port 8000 already in use
**Fix:**
```powershell
# Kill existing process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Or use different port
uvicorn ui.api.server:app --port 8001
```

### Issue: Dashboard shows "Loading..." forever
**Cause:** Backend not running

**Fix:**
```powershell
# Terminal 1: Start backend
uvicorn ui.api.server:app --reload

# Terminal 2: Start frontend
cd ui\frontend
npm run dev
```

### Issue: CORS errors in browser console
**Fix:** Add to `ui/api/server.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔒 Security Notes

### API Keys
- **Never commit** `.env` file to Git
- Use environment variables or secure key vaults
- Rotate keys regularly

### Production Deployment
- Use HTTPS for all endpoints
- Implement authentication (OAuth2/JWT)
- Rate limit API endpoints
- Sanitize all user inputs
- Use secrets management (AWS Secrets Manager, Azure Key Vault)

---

## 🧪 Testing

### Unit Tests
```powershell
# Run validation suite
python scripts\validate_ouroboros.py
```

### Integration Tests
```powershell
# Generate small test batch
python scripts\run_curved_curriculum.py --count 5

# Verify quality
python scripts\verify_harvest.py data\harvests\curriculum_*.jsonl
```

### End-to-End Test
```powershell
# Full Ouroboros run (2 iterations)
python scripts\run_ouroboros.py --batch 10 --iters 2

# Launch dashboard and verify metrics
.\ui\launch_dashboard.ps1
```

---

## 📊 Performance Benchmarks

### Generation Speed (gpt-4o)
- **Euclidean:** ~30 seconds per sample
- **Curved:** ~45 seconds per sample (includes seed generation)
- **Fusion:** ~60 seconds per sample (combines multiple seeds)

### Batch Processing
- **10 samples:** ~5-8 minutes
- **50 samples:** ~25-40 minutes
- **100 samples:** ~50-80 minutes

### Hardware Requirements
- **Minimum:** 8GB RAM, 2 CPU cores
- **Recommended:** 16GB RAM, 4+ CPU cores
- **Optimal:** 32GB RAM, 8+ CPU cores, GPU

---

## 🔄 Update & Maintenance

### Update Dependencies
```powershell
# Python
pip install --upgrade -r requirements.txt

# Frontend
cd ui\frontend
npm update
cd ..\..
```

### Pull Latest Changes
```powershell
git pull origin main
pip install -r requirements.txt
cd ui\frontend
npm install
cd ..\..
```

### Clean Build
```powershell
# Remove Python cache
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Remove frontend build
Remove-Item -Recurse -Force ui\frontend\dist, ui\frontend\node_modules

# Reinstall
cd ui\frontend
npm install
npm run build
```

---

## 🌐 Deployment

### Production Build
```powershell
# Frontend
cd ui\frontend
npm run build
cd ..\..

# Backend (with gunicorn)
pip install gunicorn
gunicorn ui.api.server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (Optional)
```dockerfile
# Dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "ui.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```powershell
docker build -t ouroboros-backend .
docker run -p 8000:8000 ouroboros-backend
```

### Cloud Deployment
- **Backend:** AWS Lambda, Google Cloud Run, Azure Functions
- **Frontend:** Vercel, Cloudflare Pages, Netlify
- **Storage:** AWS S3, Google Cloud Storage, Azure Blob

---

## 📖 Next Steps

After installation:

1. **Read Documentation:**
   - `README_OUROBOROS.md` - Main guide
   - `ARCHITECTURE.md` - System architecture
   - `PHASE_II_COMPLETE.md` - Phase II summary

2. **Run Tutorials:**
   - Generate initial dataset
   - Launch Ouroboros feedback loop
   - Monitor via dashboard

3. **Customize:**
   - Adjust hyperparameters
   - Add custom curvature types
   - Extend dashboard components

---

## 🆘 Support

### Documentation
- **Main README:** `README_OUROBOROS.md`
- **Frontend Guide:** `ui/frontend/README.md`
- **API Docs:** `http://localhost:8000/docs` (when running)

### Community
- **GitHub Issues:** [Report bugs](https://github.com/Kinrokin/kings-theorem/issues)
- **Discussions:** [Ask questions](https://github.com/Kinrokin/kings-theorem/discussions)

### Debug Mode
```powershell
# Verbose logging
$env:LOG_LEVEL = "DEBUG"
python scripts\run_ouroboros.py --verbose

# Frontend dev tools
# Press F12 in browser → Console tab
```

---

## ✅ Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Repository cloned
- [ ] Python virtual environment created and activated
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install` in `ui/frontend/`)
- [ ] `.env` file created with API keys
- [ ] Validation tests pass (`python scripts\validate_ouroboros.py`)
- [ ] Backend starts successfully (`uvicorn ui.api.server:app`)
- [ ] Frontend starts successfully (`npm run dev`)
- [ ] Dashboard loads at `http://localhost:5173`

**All checked? You're ready to generate sovereign intelligence!** 🐍

---

**Installation complete. The Ouroboros Protocol awaits your command.**

🚀 **Next:** `python scripts\run_ouroboros.py --help`
