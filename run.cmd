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

set "EGG_LINK=.venv\Lib\site-packages\spectral_analysis_app.egg-link"
set "DIST_INFO_PATTERN=.venv\Lib\site-packages\spectral_analysis_app-*.dist-info"

set "INSTALL_NEEDED=1"
if exist "%EGG_LINK%" (
    set "INSTALL_NEEDED=0"
) else (
    for /f "delims=" %%D in ('dir /b /ad "%DIST_INFO_PATTERN%" 2^>nul') do (
        set "INSTALL_NEEDED=0"
    )
)

if "!INSTALL_NEEDED!"=="1" (
    echo Installing dependencies...
    pip install -e .
    if errorlevel 1 (
        echo Failed to install dependencies.
        popd >nul
        exit /b 1
    )
)

python -m streamlit run src/spectral_app/interface/streamlit_app.py
set "STREAMLIT_EXIT_CODE=%ERRORLEVEL%"

popd >nul
endlocal & exit /b %STREAMLIT_EXIT_CODE%
