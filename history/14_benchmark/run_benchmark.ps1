param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try{
 New-Item -ItemType Directory -Force sim,logs | Out-Null
 Push-Location sim
 try{
  $files=@('../rtl/fault_v_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../verify/tb_benchmark.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_benchmark -s tb_benchmark --debug typical --mt off
  if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_benchmark -runall -log tb_benchmark.log
  if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
  $s=Get-Content tb_benchmark.log -Raw
  if($s -match 'Fatal:' -or !$s.Contains('ALL 48 BENCHMARK RUNS PASSED')){throw 'Benchmark acceptance failed'}
  Copy-Item tb_benchmark.log ../logs/ -Force
 }finally{Pop-Location}
}finally{Pop-Location}
