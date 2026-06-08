@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install flask flask-wtf flask-sqlalchemy pymysql cryptography
pip freeze > requirements.txt
echo.
echo Setup complete!
echo To run: 
echo    venv\Scripts\activate
echo    python app.py
pause