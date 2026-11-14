param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force gate_sim | Out-Null
 Push-Location gate_sim
 try {
  & (Join-Path $VivadoBin 'xvlog.bat') -d FUNCTIONAL ../macros/primitives_xsim.v ../macros/sky130_fd_sc_hd_xsim.v ../macros/model.v ../mapped_top.v
  if($LASTEXITCODE -ne 0){throw 'Gate library compile failed'}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv ../verify/tb_gate.sv
  if($LASTEXITCODE -ne 0){throw 'Gate compile failed'}
  & (Join-Path $VivadoBin 'xelab.bat') tb_gate -s tb_gate --debug typical --mt off
  if($LASTEXITCODE -ne 0){throw 'Gate elaboration failed'}
  & (Join-Path $VivadoBin 'xsim.bat') tb_gate -runall -log tb_gate.log
  Copy-Item tb_gate.log ../logs/ -Force
  $s=Get-Content tb_gate.log -Raw
  if($LASTEXITCODE -ne 0 -or $s -match 'Fatal:' -or !$s.Contains('ALL MAPPED GATE PROGRAM CHECKS PASSED')){throw 'Gate simulation failed'}
 } finally {Pop-Location}
} finally {Pop-Location}
