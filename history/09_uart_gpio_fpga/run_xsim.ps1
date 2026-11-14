param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'sim'),(Join-Path $PSScriptRoot 'logs') | Out-Null
Push-Location (Join-Path $PSScriptRoot 'sim')
try {
    $sourceFiles=@('../rtl/fault_v_pkg.sv')
    $sourceFiles+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
    $sourceFiles+=Get-ChildItem ../board/*.sv | ForEach-Object {'../board/'+$_.Name}
    $sourceFiles+=@('../verify/tb_fpga_top.sv','../verify/tb_reset.sv','../verify/tb_fault_v_io.sv','../verify/tb_io_faults.sv')
    & (Join-Path $VivadoBin 'xvlog.bat') --sv @sourceFiles (Join-Path $VivadoBin '../data/verilog/src/glbl.v')
    if ($LASTEXITCODE -ne 0) {throw 'xvlog failed'}
    $tests=@(
        @{Top='tb_reset';Marker='ALL 60 RESET CHECKS PASSED'},
        @{Top='tb_fault_v_io';Marker='ALL 16 IO TRANSACTIONS PASSED'},
        @{Top='tb_io_faults';Marker='ALL 8 CPU IO FAULT CASES PASSED'},
        @{Top='tb_fpga_top';Marker='ALL 2 FPGA PERIPHERAL PROGRAM RUNS PASSED'}
    )
    foreach($test in $tests) {
        & (Join-Path $VivadoBin 'xelab.bat') $test.Top glbl -L unisims_ver -s $test.Top --debug typical --mt off
        if ($LASTEXITCODE -ne 0) {throw 'xelab failed'}
        & (Join-Path $VivadoBin 'xsim.bat') $test.Top -runall -log ($test.Top+'.log')
        if ($LASTEXITCODE -ne 0) {throw 'xsim failed'}
        $result=Get-Content ($test.Top+'.log') -Raw
        if ($result -match 'Fatal:' -or !$result.Contains($test.Marker)) {throw 'Missing PASS or failed simulation'}
        Copy-Item ($test.Top+'.log') ../logs/ -Force
    }
} finally {Pop-Location}
