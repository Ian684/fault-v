param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Force sim,logs | Out-Null
 Push-Location sim
 try {
  $files=@('../rtl/fault_v_pkg.sv')
  $files+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
  & (Join-Path $VivadoBin 'xvlog.bat') --sv @files ../verify/tb_custom_cpu.sv ../verify/tb_extension_reset.sv ../verify/tb_custom_program.sv
  if($LASTEXITCODE -ne 0){throw 'Compile failed'}
  $tests=@(
   @{Top='tb_custom_cpu';Marker='ALL 3822 CUSTOM CPU CASE RUNS PASSED'},
   @{Top='tb_custom_reset';Marker='ALL 52 CUSTOM CPU RESET STAGES PASSED'},
   @{Top='tb_custom_program';Marker='ALL 4 CUSTOM PROGRAM RUNS AND 4 FAULT INJECTIONS PASSED'}
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
