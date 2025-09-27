@echo off
setlocal enabledelayedexpansion

set "REPO_DIR=%~dp0"
pushd "%REPO_DIR%" >nul

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        popd >nul
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    popd >nul
    exit /b 1
)

if not exist ".venv\Lib\site-packages\spectral_app.egg-link" (
    echo Installing dependencies...
    pip install -e .
    if errorlevel 1 (
        echo Failed to install dependencies.
        popd >nul
        exit /b 1
    )
)

streamlit run -m spectral_app.interface.streamlit_app

popd >nul
endlocal
