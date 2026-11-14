param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force sim,logs | Out-Null
 Push-Location sim
 try {
  $files=@('../rtl/fault_v_pkg.sv','../rtl/a_stream_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -notin @('fault_v_pkg.sv','a_stream_pkg.sv') | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../verify/tb_stream_demo.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_stream_demo -s tb_stream_demo --debug typical --mt off
  if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_stream_demo -runall -log tb_stream_demo.log
  Copy-Item tb_stream_demo.log ../logs/ -Force
  $s=Get-Content tb_stream_demo.log -Raw
  if($LASTEXITCODE -ne 0 -or $s -match 'Fatal:' -or !$s.Contains('ALL 4 STREAM DEMO RUNS AND 4 INJECTED SELF-CHECK FAILURES PASSED')){throw 'Stream demo failed'}
 }finally{Pop-Location}
}finally{Pop-Location}
