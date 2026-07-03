@echo off
cd /d "%~dp0"
echo Pulling latest version...
git pull
echo.
echo Installing/updating dependencies...
python -m pip install -r requirements.txt
echo.
echo Update complete.
pause
