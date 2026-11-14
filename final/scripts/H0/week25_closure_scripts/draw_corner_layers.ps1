Add-Type -AssemblyName System.Drawing
$closure = Split-Path $PSScriptRoot -Parent
$geometry = Get-Content -LiteralPath (Join-Path $closure 'reports\native_corner_geometry\obstacles.json') -Raw | ConvertFrom-Json
$bitmap = New-Object System.Drawing.Bitmap 1800,1700
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.Clear([System.Drawing.Color]::White)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$font = New-Object System.Drawing.Font 'Consolas',9
$titleFont = New-Object System.Drawing.Font 'Consolas',16
$colors = @{
    net3347 = [System.Drawing.Color]::Crimson
    net5547 = [System.Drawing.Color]::RoyalBlue
    net6170 = [System.Drawing.Color]::DarkOrange
    net4319 = [System.Drawing.Color]::ForestGreen
    net3311 = [System.Drawing.Color]::Purple
    net3177 = [System.Drawing.Color]::DeepPink
    net4842 = [System.Drawing.Color]::DarkCyan
}
$leftDbu = 1576000; $bottomDbu = 634000; $rightDbu = 1596000; $topDbu = 654000
$scale = 700.0 / ($rightDbu - $leftDbu)
foreach ($index in 0..3) {
    $layer = 'met' + ($index+1)
    $plotLeft = 85 + ($index % 2) * 900
    $plotTop = 60 + [math]::Floor($index / 2) * 850
    $graphics.DrawString("$layer  (native group C)", $titleFont, [System.Drawing.Brushes]::Black, [single]$plotLeft, [single]($plotTop-40))
    $items = @($geometry.shapes | Where-Object { $_[0] -eq $layer -and $_[1] -le $rightDbu -and $_[3] -ge $leftDbu -and $_[2] -le $topDbu -and $_[4] -ge $bottomDbu })
    $ordered = @($items | Where-Object { $_[5] -like '@*' }) + @($items | Where-Object { $_[5] -notlike '@*' -and -not $colors.ContainsKey([string]$_[5]) }) + @($items | Where-Object { $colors.ContainsKey([string]$_[5]) })
    $labelled = @{}
    foreach ($shape in $ordered) {
        $owner = [string]$shape[5]
        $x1 = [math]::Max([double]$shape[1], $leftDbu); $x2 = [math]::Min([double]$shape[3], $rightDbu)
        $y1 = [math]::Max([double]$shape[2], $bottomDbu); $y2 = [math]::Min([double]$shape[4], $topDbu)
        $px = $plotLeft + ($x1-$leftDbu)*$scale; $py = $plotTop + ($topDbu-$y2)*$scale
        $pw = [math]::Max(1, ($x2-$x1)*$scale); $ph = [math]::Max(1, ($y2-$y1)*$scale)
        $color = if ($colors.ContainsKey($owner)) { $colors[$owner] } elseif ($owner -like '@*') { [System.Drawing.Color]::FromArgb(100,235,220,190) } elseif ($owner -in @('VPWR','VGND')) { [System.Drawing.Color]::FromArgb(150,30,30,30) } else { [System.Drawing.Color]::FromArgb(115,135,135,135) }
        $brush = New-Object System.Drawing.SolidBrush $color
        $graphics.FillRectangle($brush,[single]$px,[single]$py,[single]$pw,[single]$ph)
        $brush.Dispose()
        if ($colors.ContainsKey($owner) -and -not $labelled.ContainsKey($owner)) {
            $labelled[$owner] = @($px,$py)
        }
    }
    foreach ($owner in $labelled.Keys) {
        $position = $labelled[$owner]
        $brush = New-Object System.Drawing.SolidBrush $colors[$owner]
        $graphics.DrawString($owner, $font, $brush, [single]$position[0], [single]($position[1]-18))
        $brush.Dispose()
    }
    $graphics.DrawRectangle([System.Drawing.Pens]::Black,[single]$plotLeft,[single]$plotTop,[single]700,[single]700)
    foreach ($tick in 0..10) {
        $x = $plotLeft + $tick*70; $y = $plotTop + 700 - $tick*70
        $graphics.DrawString(([string](1576+$tick*2)), $font, [System.Drawing.Brushes]::Black,[single]($x-17),[single]($plotTop+705))
        $graphics.DrawString(([string](634+$tick*2)), $font, [System.Drawing.Brushes]::Black,[single]($plotLeft-40),[single]($y-6))
    }
    $cx = $plotLeft+(1583550-$leftDbu)*$scale; $cy = $plotTop+($topDbu-639710)*$scale
    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Black),2
    $graphics.DrawEllipse($pen,[single]($cx-10),[single]($cy-10),[single]20,[single]20)
    $pen.Dispose()
    $graphics.DrawString('Coordinates: um; tan: LEF obstruction; gray: other copper; circle: short', $font, [System.Drawing.Brushes]::Black,[single]$plotLeft,[single]($plotTop+750))
}
$output = Join-Path $closure 'reports\native_corner_geometry\corner_layers.png'
$bitmap.Save($output,[System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose(); $bitmap.Dispose(); $font.Dispose(); $titleFont.Dispose()
Write-Output $output
