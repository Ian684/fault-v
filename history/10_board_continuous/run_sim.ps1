param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    python ./build_program.py
    if($LASTEXITCODE -ne 0){throw 'Program generation failed'}
    New-Item -ItemType Directory -Force sim,logs | Out-Null
    Push-Location sim
    try {
        $files=@('../rtl/fault_v_pkg.sv')
        $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
        $files+='../verify/tb_board_loop.sv'
        & (Join-Path $VivadoBin 'xvlog.bat') --sv @files
        if($LASTEXITCODE -ne 0){throw 'Compile failed'}
        & (Join-Path $VivadoBin 'xelab.bat') tb_board_loop -s tb_board_loop --debug typical --mt off
        if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
        & (Join-Path $VivadoBin 'xsim.bat') tb_board_loop -runall -log tb_board_loop.log
        if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
        Copy-Item tb_board_loop.log ../logs/ -Force
        $result=Get-Content tb_board_loop.log -Raw
        if($result -match 'Fatal:' -or !$result.Contains('ALL BOARD LOOP CHECKS PASSED')){throw 'Verification did not pass'}
    } finally {Pop-Location}
} finally {Pop-Location}
