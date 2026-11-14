param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    python ./build_stress.py
    if ($LASTEXITCODE -ne 0) {throw 'Stress image generation failed'}
    New-Item -ItemType Directory -Force sim,logs | Out-Null
    Push-Location sim
    try {
        $files=@('../rtl/fault_v_pkg.sv')
        $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
        $files+='../verify/tb_stress.sv'
        & (Join-Path $VivadoBin 'xvlog.bat') --sv @files
        if ($LASTEXITCODE -ne 0) {throw 'xvlog failed'}
        & (Join-Path $VivadoBin 'xelab.bat') tb_stress -s tb_stress --debug typical --mt off
        if ($LASTEXITCODE -ne 0) {throw 'xelab failed'}
        & (Join-Path $VivadoBin 'xsim.bat') tb_stress -runall -log tb_stress.log
        if ($LASTEXITCODE -ne 0) {throw 'xsim failed'}
        Copy-Item tb_stress.log ../logs/tb_stress.log -Force
        $result=Get-Content tb_stress.log -Raw
        if ($result -match 'Fatal:' -or !$result.Contains('ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED')) {
            throw 'Stress simulation failed or final PASS missing'
        }
    } finally {Pop-Location}
} finally {Pop-Location}
