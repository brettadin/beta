@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"

pip install -e .

streamlit run -m spectral_app.interface.streamlit_app
