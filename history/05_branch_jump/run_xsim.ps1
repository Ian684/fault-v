param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$taskSim=Join-Path $taskRoot 'sim'
New-Item -ItemType Directory -Path $taskSim -Force | Out-Null
Push-Location $taskSim
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv -i ../verify ../rtl/fault_v_pkg.sv ../rtl/control_fsm.sv ../rtl/decoder.sv ../rtl/alu.sv ../rtl/imm_gen.sv ../rtl/regfile.sv ../rtl/pc_reg.sv ../rtl/branch_compare.sv ../rtl/fault_v_cpu.sv ../verify/tb_branch_cpu.sv
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    & (Join-Path $VivadoBin 'xelab.bat') tb_branch_cpu -s branch_cpu_behav --debug typical --mt off
    if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
    & (Join-Path $VivadoBin 'xsim.bat') branch_cpu_behav -runall -log branch_cpu_results.log
    if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
    $taskLog=Get-Content 'branch_cpu_results.log' -Raw
    if ($taskLog -match 'Fatal:' -or $taskLog -notmatch 'ALL 134 BRANCH CPU SCENARIOS PASSED') { throw 'Required PASS marker missing or simulation failed' }
    New-Item -ItemType Directory -Path (Join-Path $taskRoot 'logs') -Force | Out-Null
    Copy-Item -LiteralPath 'branch_cpu_results.log' -Destination (Join-Path $taskRoot 'logs/branch_cpu_results.log') -Force
} finally { Pop-Location }
