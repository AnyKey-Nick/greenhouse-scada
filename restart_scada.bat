@echo off
echo Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting SCADA with new layout...
cd /d "D:\Download\Data\Other\SNU2\DIPLOM\Ap1"
python app.py --scada

pause
