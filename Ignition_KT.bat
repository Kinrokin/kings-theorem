@echo off

TITLE King's Theorem v53.6 - Auto-Ignition Sequence

COLOR 0A

echo =================================================

echo   KING'S THEOREM v53.6 (AUDIT-PLATINUM)

echo   Initiating Autonomous Launch Protocol...

echo =================================================

:: 1. Start Docker Backend (The Body)

echo.

echo [-] Waking the Infrastructure (Docker)...

cd /d "%~dp0docker"

docker-compose up -d

:: 2. Wait for Docker to settle

echo [-] Stabilizing Neural Link (Waiting 10s)...

timeout /t 10 /nobreak >nul

:: 3. Load the Brain (The Student)

echo [-] Injecting Qwen 2.5 Intelligence...

docker exec -d docker-ollama-qwen-1 ollama run qwen2.5:3b

:: 4. Launch the UI (The Face)

echo [-] Opening Cognitive Cockpit...

cd /d "%~dp0"

start http://localhost:8501

streamlit run ui_app.py

pause
