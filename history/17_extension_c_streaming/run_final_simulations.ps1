param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
foreach($script in @('run_stream_demo.ps1','run_streams.ps1','run_payload.ps1','run_applications.ps1')) {
 $log=Join-Path $PSScriptRoot ('logs/'+$script.Replace('.ps1','')+'_console.txt')
 & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $script) -VivadoBin $VivadoBin *> $log
 if($LASTEXITCODE -ne 0){throw ('Failed '+$script+'; see '+$log)}
 Write-Output ('PASS '+$script)
}
