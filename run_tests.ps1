$services = "auth-service","user-service","transaction-service","analytics-service","notification-service"
$fail = 0
foreach ($svc in $services) {
    Write-Host "=== $svc ==="
    Push-Location $svc
    pytest -q
    if ($LASTEXITCODE -ne 0) { $fail = 1 }
    Pop-Location
}
exit $fail