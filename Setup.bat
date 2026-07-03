@echo off
cls
echo =====================================================================
echo                       PASSMANAGE SETUP 
echo =====================================================================
echo.

:: 1. Check if the virtual environment already exists
if exist venv\Scripts\activate.bat (
    echo => [INFO] Found existing virtual environment. Moving to activation...
    goto activate
)

:: 2. Try creating the venv using 'python'
echo => [1/4] Attempting environment creation via 'python'...
python -m venv venv >nul 2>&1

:: 3. Fallback to 'py' if 'python' didn't work
if not exist venv\Scripts\activate.bat (
    echo => [INFO] 'python' command skipped. Trying 'py' launcher instead...
    py -m venv venv >nul 2>&1
)

:: 4. Safety verification check
if not exist venv\Scripts\activate.bat (
    echo.
    echo [ERROR] Windows could not generate the 'venv' directory automatically.
    echo This means Python is installed but its path isn't exposed to your system command line.
    echo.
    echo To fix this, reinstall Python and check the box that says:
    echo "Add python.exe to PATH"
    echo.
    pause
    exit /b
)

:activate
echo => [2/4] Activating local environment boundary...
call venv\Scripts\activate

echo => [3/4] Installing all required secure web packages...
pip install flask flask-sqlalchemy flask-login flask-wtf cryptography werkzeug

echo => [4/4] Activating Application Control Center...
echo ---------------------------------------------------------------------
echo  SUCCESS: Server is launching on http://127.0.0.1:5000
echo ---------------------------------------------------------------------
echo.

python app.py
pause