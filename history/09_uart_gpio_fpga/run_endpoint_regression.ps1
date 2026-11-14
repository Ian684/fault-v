param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
New-Item -ItemType Directory -Path (Join-Path $taskRoot 'sim') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $taskRoot 'logs') -Force | Out-Null
Push-Location (Join-Path $taskRoot 'sim')
try {
    & (Join-Path $VivadoBin 'xvlog.bat') --sv -i ../verify ../rtl/fault_v_pkg.sv ../rtl/control_fsm.sv ../rtl/decoder.sv ../rtl/alu.sv ../rtl/imm_gen.sv ../rtl/regfile.sv ../rtl/pc_reg.sv ../rtl/branch_compare.sv ../rtl/load_extract.sv ../rtl/store_align.sv ../rtl/fault_v_cpu.sv ../rtl/fault_v_memory.sv ../rtl/uart_tx.sv ../rtl/fault_v_io.sv ../rtl/fault_v_soc.sv ../verify/tb_fault_v_soc.sv ../verify/tb_fault_v_memory.sv
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    $taskTests=@(
        @{Top='tb_fault_v_soc'; Snapshot='fault_v_soc_behav'; Log='soc_results.log'; Marker='ALL 12 SOC PROGRAM RUNS PASSED'},
        @{Top='tb_fault_v_memory'; Snapshot='fault_v_memory_behav'; Log='endpoint_results.log'; Marker='ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED'}
    )
    foreach ($taskTest in $taskTests) {
        & (Join-Path $VivadoBin 'xelab.bat') $taskTest.Top -s $taskTest.Snapshot --debug typical --mt off
        if ($LASTEXITCODE -ne 0) { throw 'xelab failed' }
        & (Join-Path $VivadoBin 'xsim.bat') $taskTest.Snapshot -runall -log $taskTest.Log
        if ($LASTEXITCODE -ne 0) { throw 'xsim failed' }
        $taskLog=Get-Content -LiteralPath $taskTest.Log -Raw
        if ($taskLog -match 'Fatal:' -or !$taskLog.Contains($taskTest.Marker)) { throw 'Test failed or missing PASS marker' }
        Copy-Item -LiteralPath $taskTest.Log -Destination (Join-Path $taskRoot ('logs/'+$taskTest.Log)) -Force
    }
} finally { Pop-Location }

