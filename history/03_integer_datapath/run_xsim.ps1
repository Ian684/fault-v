param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskSim=Join-Path $taskRoot 'sim'
New-Item -ItemType Directory -Path $taskSim -Force | Out-Null
Push-Location $taskSim
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv -i ../verify ../rtl/fault_v_pkg.sv ../rtl/control_fsm.sv ../rtl/decoder.sv ../rtl/alu.sv ../rtl/imm_gen.sv ../rtl/regfile.sv ../rtl/pc_reg.sv ../rtl/fault_v_cpu.sv ../verify/tb_fault_v_cpu.sv
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoBin 'xelab.bat') tb_fault_v_cpu -s integer_cpu_behav --debug typical --mt off
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') integer_cpu_behav -runall -log integer_cpu_results.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $taskLog=Get-Content 'integer_cpu_results.log' -Raw
    if ($taskLog -match 'Fatal:' -or $taskLog -notmatch 'ALL 11 INTEGER CPU PROGRAM SCENARIOS PASSED') { throw 'CPU test did not reach the required PASS marker' }
    New-Item -ItemType Directory -Path (Join-Path $taskRoot 'logs') -Force | Out-Null
    Copy-Item -LiteralPath 'integer_cpu_results.log' -Destination (Join-Path $taskRoot 'logs/integer_cpu_results.log') -Force
} finally { Pop-Location }
