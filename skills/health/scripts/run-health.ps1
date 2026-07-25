param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("collect", "agent-context", "maintainability", "doc-refs", "verifier-output")]
    [string]$Action,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$ErrorActionPreference = "Stop"

function Find-GitRoot([string]$Executable) {
    if (-not $Executable) {
        return $null
    }

    $fullPath = [IO.Path]::GetFullPath($Executable)
    $current = if (Test-Path -LiteralPath $fullPath -PathType Container) {
        $fullPath
    } else {
        Split-Path -Parent $fullPath
    }
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

function Resolve-Executable([string]$Candidate) {
    if (-not $Candidate) {
        return $null
    }
    if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
        return (Resolve-Path -LiteralPath $Candidate).Path
    }
    $command = Get-Command $Candidate -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    return $null
}

function Find-Python {
    $override = Resolve-Executable $env:WAZA_PYTHON
    if ($override) {
        return $override
    }
    foreach ($name in @("python3.exe", "python.exe", "py.exe")) {
        $executable = Resolve-Executable $name
        if ($executable) {
            return $executable
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

$scriptNames = @{
    "collect" = "collect-data.sh"
    "agent-context" = "check-agent-context.sh"
    "maintainability" = "check-maintainability.sh"
    "doc-refs" = "check-doc-refs.sh"
    "verifier-output" = "check-verifier-output.sh"
}
$scriptName = $scriptNames[$Action]
$scriptPath = Join-Path $PSScriptRoot $scriptName
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
    [Console]::Error.WriteLine("Health runtime script not found: $scriptPath")
    exit 1
}

$bashPath = $null
$childPath = $env:PATH
$pythonPath = $null
$isWindowsHost = $env:OS -eq "Windows_NT"
if ($isWindowsHost) {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    $bash = Get-Command bash.exe -ErrorAction SilentlyContinue
    $gitRoot = Find-GitRoot $env:GIT_INSTALL_ROOT
    if (-not $gitRoot) {
        $gitRoot = Find-GitRoot $(if ($git) { $git.Source } else { $null })
    }
    if (-not $gitRoot) {
        $gitRoot = Find-GitRoot $(if ($bash) { $bash.Source } else { $null })
    }
    if (-not $gitRoot -and $git) {
        $gitExecPath = & $git.Source --exec-path 2>$null
        if ($LASTEXITCODE -eq 0) {
            $gitRoot = Find-GitRoot $gitExecPath
        }
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

$env:PATH = $childPath
if ($pythonPath) {
    $env:WAZA_PYTHON = $pythonPath.Replace("\", "/")
}

& $bashPath $scriptPath @ScriptArgs
exit $LASTEXITCODE
