# Iterate: N64Recomp -> harvest missing function boundaries from "Tail call" infos
# -> add to splat symbol_addrs.txt -> re-split -> regen symbols -> retry.
# Stops when N64Recomp exits 0 or no new addresses are learned.
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
for ($i = 1; $i -le 25; $i++) {
    & .\N64Recomp.exe revenge.toml > recomp-out.txt 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Host "=== CLEAN RECOMPILE after $i iteration(s) ==="; exit 0 }
    $targets = Select-String -Path recomp-out.txt -Pattern 'Tail call in \S+ to (0x[0-9A-Fa-f]+)' |
        ForEach-Object { $_.Matches[0].Groups[1].Value } | Sort-Object -Unique
    $existing = Get-Content disasm\symbol_addrs.txt -ErrorAction SilentlyContinue
    $new = @()
    foreach ($t in $targets) {
        $addr = [uint32]$t
        $line = ('func_{0:X8} = 0x{0:X8}; // type:func' -f $addr)
        if ($existing -notcontains $line) { $new += $line }
    }
    if ($new.Count -eq 0) {
        Write-Host "=== STUCK at iteration $i - no new addresses; last errors: ==="
        Select-String -Path recomp-out.txt -Pattern 'Error' | Select-Object -First 5 | ForEach-Object Line
        exit 1
    }
    Add-Content disasm\symbol_addrs.txt $new
    Write-Host "iter ${i}: +$($new.Count) function boundaries ($($new -join ', '))"
    Set-Location disasm
    Remove-Item -Recurse -Force asm -ErrorAction SilentlyContinue
    & .\.venv\Scripts\python.exe -m splat split revenge.yaml *> $null
    Set-Location $root
    python tools\gen_symbols.py > $null
}
Write-Host "=== iteration cap reached ==="
exit 1
