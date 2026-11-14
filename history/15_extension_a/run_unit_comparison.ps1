param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force comparison_sim,logs | Out-Null
 Push-Location comparison_sim
 try {
  & (Join-Path $VivadoBin 'xvlog.bat') --sv ../rtl/fault_v_pkg.sv ../comparison/shared_unit.sv ../comparison/parallel_unit.sv ../verify/tb_unit_comparison.sv
  if($LASTEXITCODE -ne 0){throw 'Comparison compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_unit_comparison -s tb_unit_comparison --debug typical --mt off
  if($LASTEXITCODE -ne 0){throw 'Comparison elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_unit_comparison -runall -log tb_unit_comparison.log
  if($LASTEXITCODE -ne 0){throw 'Comparison simulation failed'}
  $s=Get-Content tb_unit_comparison.log -Raw
  if($s -match 'Fatal:' -or !$s.Contains('ALL 16398 SHARED/PARALLEL UNIT COMPARISONS PASSED')){throw 'Comparison acceptance failed'}
  Copy-Item tb_unit_comparison.log ../logs/ -Force
 }finally{Pop-Location}
 & (Join-Path $VivadoBin 'vivado.bat') -mode batch -source comparison/audit.tcl -log logs/unit_audit.log -journal logs/unit_audit.jou
 if($LASTEXITCODE -ne 0){throw 'Unit resource audit failed'}
 if(!(Get-Content logs/unit_audit.log -Raw).Contains('ISOLATED UNIT RESOURCE COMPARISON PASSED')){throw 'Audit acceptance missing'}
}finally{Pop-Location}
