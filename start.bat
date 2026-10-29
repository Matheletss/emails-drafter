@echo off
echo Starting Gmail Drafting Agent...

cd backend
start cmd /k ".\venv\Scripts\activate && uvicorn main:app --reload --port 8000"

cd ..\frontend
start cmd /k "npm run dev"

echo Both backend and frontend have been started in separate windows!
pause
