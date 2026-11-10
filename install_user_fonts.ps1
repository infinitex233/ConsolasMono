$ErrorActionPreference = 'Stop'

$sourceDir = Join-Path $PSScriptRoot 'dist'
$fontDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$registryKey = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

$fonts = @(
    @{ File = 'ConsolasMono-Regular.ttf';    Name = 'Consolas Mono (TrueType)' },
    @{ File = 'ConsolasMono-Bold.ttf';       Name = 'Consolas Mono Bold (TrueType)' },
    @{ File = 'ConsolasMono-Italic.ttf';     Name = 'Consolas Mono Italic (TrueType)' },
    @{ File = 'ConsolasMono-BoldItalic.ttf'; Name = 'Consolas Mono Bold Italic (TrueType)' }
)

New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
if (-not (Test-Path $registryKey)) {
    New-Item -Path $registryKey -Force | Out-Null
}

Add-Type -Namespace Win32 -Name User32 -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern int AddFontResource(string lpFilename);
[DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool RemoveFontResource(string lpFilename);
[DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam, uint fuFlags, uint uTimeout, out IntPtr lpdwResult);
'@

$HWND_BROADCAST = [IntPtr]0xFFFF
$WM_FONTCHANGE = 0x001D
$SMTO_ABORTIFHUNG = 0x0002

foreach ($font in $fonts) {
    $source = Join-Path $sourceDir $font.File
    if (-not (Test-Path $source)) {
        throw "Missing font file: $source"
    }

    $destination = Join-Path $fontDir $font.File
    $copyNeeded = $true
    if (Test-Path $destination) {
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        if ($sourceHash -eq $destinationHash) {
            $copyNeeded = $false
            Write-Output ("Already present: {0}" -f $destination)
        }
    }
    if ($copyNeeded) {
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }

    New-ItemProperty -Path $registryKey -Name $font.Name -Value $destination -PropertyType String -Force | Out-Null

    # Idempotent: drop any previously registered copy, then register the new one.
    [Win32.User32]::RemoveFontResource($destination) | Out-Null
    $added = [Win32.User32]::AddFontResource($destination)
    if ($added -lt 1) {
        Write-Warning "AddFontResource returned $added for $destination"
    }

    Write-Output ("Installed {0} -> {1}" -f $font.Name, $destination)
}

$queryResult = [IntPtr]::Zero
[Win32.User32]::SendMessageTimeout(
    $HWND_BROADCAST, $WM_FONTCHANGE, [IntPtr]::Zero, [IntPtr]::Zero,
    $SMTO_ABORTIFHUNG, 5000, [ref]$queryResult
) | Out-Null

Write-Output 'Font change broadcast sent.'
