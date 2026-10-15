@echo off
echo ==========================================
echo    LOOKIFY - STARTING ALL SERVICES
echo ==========================================

echo [1/5] Starting Main Web Server (Port 8000)...
start "Lookify - Main Server" python Frontend/server.py

echo [2/5] Starting Auth Backend (Port 5000)...
start "Lookify - Auth Backend" python backend.py

echo [3/5] Starting Search API (Port 8002)...
start "Lookify - Search API" python Frontend/search_server.py

echo [4/5] Starting Fashion Recommender (Streamlit)...
start "Lookify - Recommender" streamlit run app.py

echo [5/5] Starting Payment Service (Port 5001)...
if exist "..\RealTimePayment" (
    start "Lookify - Payment" cmd /k "cd ..\RealTimePayment && python app.py"
) else (
    echo [Info] RealTimePayment directory not found, built-in payment handled by Main Server.
)

echo.
echo All services launched! 
echo Waiting for servers to initialize...
timeout /t 5
echo.
echo Opening Lookify...
start http://127.0.0.1:8000/signin.html
