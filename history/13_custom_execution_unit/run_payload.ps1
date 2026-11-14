param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force sim,logs | Out-Null
    Copy-Item programs/custom_demo.mem sim/custom_demo.mem -Force
    Push-Location sim
    try {
        $files=@('../rtl/fault_v_pkg.sv')
        $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
        $files+=@('../board/fault_v_reset.sv','../board/fault_v_payload.sv','../verify/tb_payload.sv')
        & (Join-Path $VivadoBin 'xvlog.bat') --sv @files
        if($LASTEXITCODE -ne 0){throw 'Compile failed'}
        & (Join-Path $VivadoBin 'xelab.bat') tb_payload -s tb_payload --debug typical --mt off
        if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
        & (Join-Path $VivadoBin 'xsim.bat') tb_payload -runall -log tb_payload.log
        if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
        Copy-Item tb_payload.log ../logs/ -Force
        $result=Get-Content tb_payload.log -Raw
        if($result -match 'Fatal:' -or !$result.Contains('ALL 3 PAYLOAD RUNS PASSED')){throw 'Payload verification failed'}
    } finally {Pop-Location}
} finally {Pop-Location}
