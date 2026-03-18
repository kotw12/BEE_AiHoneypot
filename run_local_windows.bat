@echo off
echo ====================================================
echo   Honey 3-Server Local Test Suite (Windows)
echo ====================================================

:: 1. Initialize DB for Honey Server
echo [*] Initializing Honey Server Database...
python honey_server/database/init_db.py

:: 2. Create Faux Logs directory
if not exist "honey_server\logs_faux" mkdir "honey_server\logs_faux"
if not exist "honey_server\logs_faux\access.log" echo "Internal Access Log" > "honey_server\logs_faux\access.log"

:: 3. Start Monitor Server (Port 9000)
echo [*] Launching Monitor Server (Port 9000)...
start "SOC MONITOR (9000)" cmd /k "cd monitor_server && python app.py"

:: 4. Start Honey Server (Port 8080)
echo [*] Launching Honey Server (Port 8080)...
start "HONEYPOT (8080)" cmd /k "cd honey_server && python app.py"

:: 5. Start Main Server (Port 80 - Note: May need admin or change to 8000)
echo [*] Launching Main Server (Port 80)...
start "MAIN STORE (80)" cmd /k "cd main_server && python app.py"

echo ====================================================
echo   All servers are starting in separate windows.
echo   - Main Store: http://localhost
echo   - Honeypot: http://localhost:8080
echo   - SOC Monitor: http://localhost:9000
echo ====================================================
