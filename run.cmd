cd C:/Code3/beta 
python -m venv .venv 
.venv/Scripts/Activate.ps1
C:\Code3\beta\.venv\Scripts\python.exe -m pip install --upgrade pip
pip install -e . 
python -m http.server 8501
