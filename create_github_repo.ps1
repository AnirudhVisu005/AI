param(
  [string]$RepoName = "AI",
  [string]$Visibility = "private"
)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Error "gh CLI is not installed. Install and authenticate before running this script."
  exit 1
}

Write-Host "Creating GitHub repo '$RepoName' (visibility=$Visibility) and pushing..."
gh repo create $RepoName --$Visibility --source=. --remote=origin --push

Write-Host "Done."
