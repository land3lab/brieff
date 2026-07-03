@echo off
cd /d "%~dp0"
echo Installing dependencies...
python -m pip install -r requirements.txt
echo.
echo Done. Now edit the .env file and put your OpenAI API key in it.
pause
