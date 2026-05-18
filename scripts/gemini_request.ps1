param(
    [Parameter(Mandatory = $false)]
    [string]$Prompt = "Explain how AI works in a few words",

    [Parameter(Mandatory = $false)]
    [string]$Model = "gemini-flash-latest"
)

$apiKey = $env:GEMINI_API_KEY
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = $env:GOOGLE_API_KEY
}

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Error "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment."
    exit 1
}

$uri = "https://generativelanguage.googleapis.com/v1beta/models/$Model`:generateContent"
$headers = @{
    "Content-Type" = "application/json"
    "X-goog-api-key" = $apiKey
}
$body = @{
    contents = @(
        @{
            parts = @(
                @{
                    text = $Prompt
                }
            )
        }
    )
} | ConvertTo-Json -Depth 6

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Error ("Gemini request failed: " + $_.Exception.Message)
    exit 1
}
