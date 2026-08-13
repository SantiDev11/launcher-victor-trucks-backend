Add-Type -AssemblyName System.Drawing
$exe = "dist\Graficos_VictorTrucks.exe"
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon($exe)
$stream = [System.IO.File]::OpenWrite("dist\extracted_icon.ico")
try {
    $icon.Save($stream)
} finally {
    $stream.Close()
}
$src = Get-Item "dist\extracted_icon.ico"
Write-Host ("Icono extraído del EXE: " + $src.Length + " bytes")
Write-Host ("Logo original: " + (Get-Item "logo.ico").Length + " bytes")
</arg_value></tool_call>