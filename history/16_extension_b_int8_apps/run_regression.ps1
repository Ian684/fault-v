param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force sim,logs | Out-Null
 Push-Location sim
 try {
  $files=@('../rtl/fault_v_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../verify/tb_custom_exec.sv ../verify/tb_verification_suite.sv ../verify/tb_fault_v_io.sv ../verify/tb_io_faults.sv ../verify/tb_stress.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  $tests=@(
   @{Top='tb_custom_exec';Marker='RESET CANCELLATIONS'},
   @{Top='tb_verification_suite';Marker='ALL 1372 ISA AND PROGRAM RUNS PASSED'},
   @{Top='tb_fault_v_io';Marker='ALL 16 IO TRANSACTIONS PASSED'},
   @{Top='tb_io_faults';Marker='ALL 8 CPU IO FAULT CASES PASSED'},
   @{Top='tb_stress';Marker='ALL 4 STRESS PROGRAM RUNS PASSED'}
  )
  foreach($t in $tests){
   & (Join-Path $VivadoBin 'xelab.bat') $t.Top -s $t.Top --debug typical --mt off
   if($LASTEXITCODE -ne 0){throw 'Elaboration failed'}
   & (Join-Path $VivadoBin 'xsim.bat') $t.Top -runall -log ($t.Top+'.log')
   if($LASTEXITCODE -ne 0){throw 'Simulation failed'}
   $s=Get-Content ($t.Top+'.log') -Raw
   if($s -match 'Fatal:' -or !$s.Contains($t.Marker)){throw ('Verification failed: '+$t.Top)}
   Copy-Item ($t.Top+'.log') ../logs/ -Force
  }
 }finally{Pop-Location}
}finally{Pop-Location}
