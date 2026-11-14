param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force sim_priority,logs | Out-Null
 Push-Location sim_priority
 try {
  & (Join-Path $VivadoBin 'xvlog.bat') --sv ../rtl/fault_v_uart_rx.sv ../rtl/fault_v_loader.sv ../verify/tb_loader_priority.sv
  if($LASTEXITCODE -ne 0){throw 'Priority compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_loader_priority -s tb_loader_priority --mt off
  if($LASTEXITCODE -ne 0){throw 'Priority elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_loader_priority -runall -log tb_loader_priority.log
  Copy-Item tb_loader_priority.log ../logs/ -Force
  if(!(Get-Content tb_loader_priority.log -Raw).Contains('ALL LOADER ERROR PRIORITY CHECKS PASSED')){throw 'Priority acceptance failed'}
 } finally {Pop-Location}
} finally {Pop-Location}
