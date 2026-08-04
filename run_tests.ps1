param(
    [Parameter(Mandatory = $true)]
    [string]$CoreWheel,
    [switch]$AllowDirty
)

$arguments = @("scripts/validate_repository.py", "--core-wheel", $CoreWheel)
if ($AllowDirty) {
    $arguments += "--allow-dirty"
}
& "$PSScriptRoot\.venv\Scripts\python.exe" @arguments
exit $LASTEXITCODE

