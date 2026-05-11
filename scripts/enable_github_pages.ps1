# Requires: fine-grained PAT (Repository: Administration) or classic PAT with `repo`.
# Do NOT paste token into chat. Example:
#   $env:GITHUB_TOKEN = "ghp_...."
#   .\scripts\enable_github_pages.ps1
#
# Repo: HugoLeon1199/leonquant — uses GitHub Actions workflow pages.yml.
$ErrorActionPreference = "Stop"
$owner = "HugoLeon1199"
$repo = "leonquant"
$token = $env:GITHUB_TOKEN
if (-not $token) {
    Write-Error "Set env GITHUB_TOKEN first (PAT with permission to manage Pages for this repo)."
}
$headers = @{
    Accept                 = "application/vnd.github+json"
    Authorization          = "Bearer $token"
    "X-GitHub-Api-Version" = "2022-11-28"
}
$base = "https://api.github.com/repos/$owner/$repo/pages"

$body = @{
    build_type = "workflow"
    source     = @{
        branch = "main"
        path   = "/"
    }
} | ConvertTo-Json -Depth 5

try {
    $existing = Invoke-RestMethod -Uri $base -Headers $headers -Method Get
    Write-Host "Pages already exists. build_type=$($existing.build_type)"
    Invoke-RestMethod -Uri $base -Headers $headers -Method Put -Body $body -ContentType "application/json"
    Write-Host "Updated Pages to workflow source."
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Invoke-RestMethod -Uri $base -Headers $headers -Method Post -Body $body -ContentType "application/json"
        Write-Host "Created Pages (workflow). Wait 1-3 min: https://hugoleon1199.github.io/leonquant/"
    }
    else {
        throw
    }
}
