param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("update", "collect")]
    [string]$Action,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ErrorActionPreference = "Stop"

function Find-GitRoot([string]$Executable) {
    if (-not $Executable) {
        return $null
    }

    $current = Split-Path -Parent ([IO.Path]::GetFullPath($Executable))
    while ($current) {
        if (
            (Test-Path -LiteralPath (Join-Path $current "bin\bash.exe") -PathType Leaf) -and
            (Test-Path -LiteralPath (Join-Path $current "usr\bin") -PathType Container)
        ) {
            return $current
        }
        $parent = Split-Path -Parent $current
        if (-not $parent -or $parent -eq $current) {
            break
        }
        $current = $parent
    }
    return $null
}

function Find-Python {
    if ($env:WAZA_PYTHON -and (Test-Path -LiteralPath $env:WAZA_PYTHON -PathType Leaf)) {
        return (Resolve-Path -LiteralPath $env:WAZA_PYTHON).Path
    }
    foreach ($name in @("python3.exe", "python.exe")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    $candidates = @(
        (Join-Path $env:USERPROFILE "anaconda3\python.exe"),
        (Join-Path $env:USERPROFILE "miniconda3\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\python.exe"),
        (Join-Path $env:ProgramFiles "Python*\python.exe")
    )
    foreach ($candidate in $candidates) {
        $match = Resolve-Path -Path $candidate -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) {
            return $match.Path
        }
    }
    return $null
}

$scriptName = if ($Action -eq "update") { "check-update.sh" } else { "collect-data.sh" }
$scriptPath = Join-Path $PSScriptRoot $scriptName
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    [Console]::Error.WriteLine("Health runtime script not found: $scriptPath")
    exit 1
}

$bashPath = $null
$childPath = $env:PATH
if ($IsWindows) {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    $bash = Get-Command bash.exe -ErrorAction SilentlyContinue
    $gitRoot = Find-GitRoot $git.Source
    if (-not $gitRoot) {
        $gitRoot = Find-GitRoot $bash.Source
    }
    if (-not $gitRoot) {
        [Console]::Error.WriteLine(
            "Health requires Git for Windows with bin\bash.exe; make git.exe or Git Bash discoverable."
        )
        exit 1
    }

    $bashPath = Join-Path $gitRoot "bin\bash.exe"
    $runtimePaths = @(
        (Join-Path $gitRoot "usr\bin"),
        (Join-Path $gitRoot "mingw64\bin"),
        (Join-Path $gitRoot "bin"),
        (Join-Path $gitRoot "cmd")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Container }
    $childPath = (@($runtimePaths) + @($env:PATH)) -join [IO.Path]::PathSeparator
    $pythonPath = Find-Python
} else {
    $bash = Get-Command bash -ErrorAction SilentlyContinue
    if (-not $bash) {
        [Console]::Error.WriteLine("Health requires Bash on PATH.")
        exit 1
    }
    $bashPath = $bash.Source
}

$startInfo = [Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $bashPath
$startInfo.UseShellExecute = $false
$startInfo.WorkingDirectory = (Get-Location).Path
$startInfo.ArgumentList.Add($scriptPath)
foreach ($arg in $ScriptArgs) {
    $startInfo.ArgumentList.Add($arg)
}
$startInfo.Environment["PATH"] = $childPath
if ($pythonPath) {
    $startInfo.Environment["WAZA_PYTHON"] = $pythonPath.Replace("\", "/")
}

$process = [Diagnostics.Process]::Start($startInfo)
$process.WaitForExit()
exit $process.ExitCode
