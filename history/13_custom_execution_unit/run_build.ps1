param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force logs | Out-Null
    & (Join-Path $VivadoBin 'vivado.bat') -mode batch -source build.tcl -log logs/final_build.log -journal logs/final_build.jou
    if($LASTEXITCODE -ne 0){throw 'FPGA build failed'}
    if(!(Get-Content logs/final_build.log -Raw).Contains('CUSTOM FPGA BUILD PASSED')){throw 'FPGA acceptance marker missing'}
} finally {Pop-Location}
