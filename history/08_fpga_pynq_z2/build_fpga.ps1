param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force build,logs | Out-Null
    & (Join-Path $VivadoBin 'vivado.bat') -mode batch -source build_fpga.tcl -log logs/build.log -journal logs/build.jou
    if ($LASTEXITCODE -ne 0) { throw 'Vivado build failed; see logs/build.log and build/project/*.runs/*/runme.log' }
    if (!(Test-Path build/fault_v_fpga_top.bit)) {throw 'Missing bitstream'}
} finally {Pop-Location}
