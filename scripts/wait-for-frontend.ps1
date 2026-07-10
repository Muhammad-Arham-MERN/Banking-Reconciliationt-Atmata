param(
    [string]$Url = "http://localhost:3000/upload",
    [int]$TimeoutMinutes = 3
)

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 180
        if ($response.StatusCode -eq 200) {
            Write-Host "Frontend ready." -ForegroundColor Green
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Timed out waiting for frontend. Opening browser anyway..." -ForegroundColor Yellow
exit 1
