@echo off
echo ============================================
echo  Password Manager - Setup & Launch
echo ============================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing / updating dependencies...
pip install flask flask-wtf flask-sqlalchemy cryptography
pip freeze > requirements.txt

echo.
echo Setup complete. Starting the application...
echo.
python app.py
pause