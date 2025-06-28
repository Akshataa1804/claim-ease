@echo off
echo Starting Ollama service...
start "" /B ollama serve > nul 2>&1

echo Waiting 15 seconds for model to load...
timeout /t 15 /nobreak > nul

echo Setting up Python environment...
call ..\venv\Scripts\activate

echo Starting ClaimEase UI...
cd ..
streamlit run streamlit_ui.py

echo Cleaning up...
taskkill /f /im ollama.exe > nul 2>&1
echo All processes terminated.