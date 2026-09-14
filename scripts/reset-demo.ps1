docker compose --env-file .env -f dev.docker-compose.yaml exec -T backend python -m app.seed.reset --confirm
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Demo data reset. Sign in with one of the accounts listed in README.md."
