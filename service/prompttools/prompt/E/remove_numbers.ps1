$directory = "D:\AI\ComfyUI_ROB1802\ComfyUI\custom_nodes\CJ-Nodes\service\prompttools\prompt\E"
$files = Get-ChildItem -Path $directory -Filter "*.txt" | Where-Object {
    $num = [int]($_.Name -split '-')[0]
    $num -ge 5 -and $num -le 11
}
foreach ($file in $files) {
    Write-Host "Processing file: $($file.Name)"
    $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
    $newContent = $content -replace '(?m)^(\d+):\s*', ''
    Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8 -NoNewline
    Write-Host "Done: $($file.Name)"
}
Write-Host "All files processed"