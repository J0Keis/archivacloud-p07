# =============================================================================
#  iniciar.ps1  —  Arranca backend y frontend en ventanas separadas
# -----------------------------------------------------------------------------
#  Uso:  desde la raíz del proyecto, en PowerShell:   .\iniciar.ps1
#  (o clic derecho sobre el archivo -> "Ejecutar con PowerShell")
# =============================================================================

$raiz = $PSScriptRoot

Write-Host "Iniciando BACKEND (puerto 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$raiz\backend'; .\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
)

Write-Host "Iniciando FRONTEND (puerto 5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$raiz\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Listo. Se abrieron dos ventanas (backend y frontend)." -ForegroundColor Green
Write-Host "Abre en el navegador:  http://localhost:5173" -ForegroundColor Green
