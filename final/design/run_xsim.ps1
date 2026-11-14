param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force sim,logs | Out-Null
 Push-Location sim
 try {
  $files=@('../rtl/fault_v_pkg.sv','../rtl/a_stream_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -notin @('fault_v_pkg.sv','a_stream_pkg.sv') | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../macros/model.v ../verify/tb_sram_banks.sv ../verify/tb_asic_boot.sv ../verify/tb_mem_arbiter.sv ../verify/tb_loader_priority.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  foreach($top in @('tb_mem_arbiter','tb_sram_banks','tb_asic_boot','tb_loader_priority')){
   & (Join-Path $VivadoBin 'xelab.bat') $top -s $top --debug typical --mt off
   if($LASTEXITCODE -ne 0){throw ('Elaboration failed '+$top)}
   & (Join-Path $VivadoBin 'xsim.bat') $top -runall -log ($top+'.log')
   Copy-Item ($top+'.log') ../logs/ -Force
   $s=Get-Content ($top+'.log') -Raw
   if($LASTEXITCODE -ne 0 -or $s -match 'Fatal:' -or !$s.Contains('ALL ')){throw ('Acceptance failed '+$top)}
  }
 } finally {Pop-Location}
} finally {Pop-Location}
