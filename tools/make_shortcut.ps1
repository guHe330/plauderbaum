# Creates "Plauderbaum.lnk" in the project folder: starts run.bat with the app icon.
# Copy the shortcut to the desktop or pin it to the taskbar as you like.
$root = Split-Path $PSScriptRoot -Parent
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$root\Plauderbaum.lnk")
$shortcut.TargetPath = "$root\run.bat"
$shortcut.WorkingDirectory = $root
$shortcut.IconLocation = "$root\assets\icon.ico"
$shortcut.WindowStyle = 7  # start the console minimized
$shortcut.Description = "Plauderbaum"
$shortcut.Save()
"Created $root\Plauderbaum.lnk"
