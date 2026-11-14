param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
New-Item -ItemType Directory -Path (Join-Path $taskRoot 'sim') -Force | Out-Null
Push-Location (Join-Path $taskRoot 'sim')
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv ../rtl/fault_v_pkg.sv ../rtl/control_fsm.sv ../rtl/decoder.sv ../rtl/alu.sv ../rtl/imm_gen.sv ../rtl/regfile.sv ../rtl/pc_reg.sv ../rtl/branch_compare.sv ../rtl/load_extract.sv ../rtl/store_align.sv ../rtl/fault_v_cpu.sv ../rtl/fault_v_memory.sv ../rtl/fault_v_soc.sv ../verify/tb_verification_suite.sv
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoBin 'xelab.bat') tb_verification_suite -s verification_suite_behav --debug typical --mt off
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') verification_suite_behav -runall -log verification_results.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $taskLog=Get-Content 'verification_results.log' -Raw
    if ($taskLog -match 'Fatal:' -or !$taskLog.Contains('ALL 1372 ISA AND PROGRAM RUNS PASSED')) { throw 'Test failed or missing PASS marker' }
    if (!$taskLog.Contains('COVERAGE mode=0 names=40/40') -or !$taskLog.Contains('COVERAGE mode=1 names=40/40')) { throw 'Instruction name coverage incomplete' }
    New-Item -ItemType Directory -Path (Join-Path $taskRoot 'logs') -Force | Out-Null
    Copy-Item -LiteralPath 'verification_results.log' -Destination (Join-Path $taskRoot 'logs/verification_results.log') -Force
} finally { Pop-Location }
