param(
    [string]$VivadoBin = 'C:\Xilinx\Vivado\2022.2\bin',
    [switch]$RegressionOnly
)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$simDir = Join-Path $taskRoot 'sim'
New-Item -ItemType Directory -Path $simDir -Force | Out-Null
Push-Location $simDir
try {
    $designFiles = @(
        '../rtl/fault_v_pkg.sv', '../rtl/decoder.sv',
        '../rtl/alu.sv', '../rtl/imm_gen.sv',
        '../rtl/regfile.sv', '../rtl/pc_reg.sv', '../rtl/pc_path.sv'
    )
    $tops = @('tb_decoder','tb_decode_path','tb_alu','tb_imm_gen','tb_regfile','tb_pc_reg','tb_pc_path')
    if ($RegressionOnly) { $tops = @('tb_alu','tb_imm_gen','tb_regfile','tb_pc_reg','tb_pc_path') }
    $testFiles = @($tops | ForEach-Object { "../verify/$_.sv" })
    & (Join-Path $VivadoBin 'xvlog.bat') --sv @designFiles @testFiles
    if ($LASTEXITCODE -ne 0) { throw 'xvlog failed' }
    foreach ($top in $tops) {
        $snapshot = "${top}_verified"
        & (Join-Path $VivadoBin 'xelab.bat') $top -s $snapshot --debug typical --mt off
        if ($LASTEXITCODE -ne 0) { throw "xelab failed: $top" }
        $logName = "${top}_results.log"
        & (Join-Path $VivadoBin 'xsim.bat') $snapshot -runall -log $logName
        if ($LASTEXITCODE -ne 0) { throw "xsim failed: $top" }
        $logText = Get-Content -LiteralPath $logName -Raw
        if ($logText -notmatch 'ALL [0-9]+ .* PASSED') { throw "Missing completion marker: $top" }
        if ($logText -match '(?m)^Fatal:|^ERROR:|FAIL |TIMEOUT ') { throw "Simulation failure: $top" }
    }
} finally {
    Pop-Location
}
