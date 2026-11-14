param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 Push-Location sim
 try {
  $files=@('../rtl/fault_v_pkg.sv','../rtl/a_stream_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -notin @('fault_v_pkg.sv','a_stream_pkg.sv') | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../macros/model.v ../verify/tb_asic_streams.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_asic_streams -s tb_asic_streams --debug typical --mt off
  if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_asic_streams -runall -log tb_asic_streams.log
  Copy-Item tb_asic_streams.log ../logs/ -Force
  $s=Get-Content tb_asic_streams.log -Raw
  if($LASTEXITCODE -ne 0 -or $s -match 'Fatal:' -or !$s.Contains('ALL STREAM SCENARIO RUNS PASSED')){throw 'ASIC stream regression failed'}
 } finally {Pop-Location}
} finally {Pop-Location}
