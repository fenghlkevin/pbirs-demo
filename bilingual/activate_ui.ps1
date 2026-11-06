$ErrorActionPreference='Stop'
$root='C:\ProgramData\P4DemoApp'
Copy-Item "$root\app\index.html" "$root\index-before-bilingual-ui-fix.html" -Force
Expand-Archive "$root\bilingual-ui-fix.zip" "$root\app" -Force
(Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/).StatusCode
