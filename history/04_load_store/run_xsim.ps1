param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
New-Item -ItemType Directory -Path (Join-Path $taskRoot 'sim') -Force | Out-Null
Push-Location (Join-Path $taskRoot 'sim')
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv -i ../verify ../rtl/fault_v_pkg.sv ../rtl/control_fsm.sv ../rtl/decoder.sv ../rtl/alu.sv ../rtl/imm_gen.sv ../rtl/regfile.sv ../rtl/pc_reg.sv ../rtl/branch_compare.sv ../rtl/load_extract.sv ../rtl/store_align.sv ../rtl/fault_v_cpu.sv ../verify/tb_memory_cpu.sv
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoBin 'xelab.bat') tb_memory_cpu -s memory_cpu_behav --debug typical --mt off
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') memory_cpu_behav -runall -log memory_cpu_results.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $taskLog=Get-Content 'memory_cpu_results.log' -Raw
    if ($taskLog -match 'Fatal:' -or $taskLog -notmatch 'ALL 252 MEMORY CPU SCENARIOS PASSED') { throw 'Required PASS marker missing or test failed' }
    New-Item -ItemType Directory -Path (Join-Path $taskRoot 'logs') -Force | Out-Null
    Copy-Item -LiteralPath 'memory_cpu_results.log' -Destination (Join-Path $taskRoot 'logs/memory_cpu_results.log') -Force
} finally { Pop-Location }
