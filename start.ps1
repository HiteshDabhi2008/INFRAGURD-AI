$ErrorActionPreference = "Stop"

Write-Host "Initializing database and seeding data..."
python -c "from backend.services.data_ingest import initialize_database; initialize_database()"

Write-Host "Starting backend on port 8000..."
Start-Process powershell -ArgumentList "-NoExit -Command `"python -m uvicorn backend.main:app --port 8000`""

Write-Host "Starting frontend on port 5173..."
Set-Location frontend
Start-Process powershell -ArgumentList "-NoExit -Command `"npm run dev -- --port 5173`""

Write-Host "Services started! Backend on 8000, Frontend on 5173."

