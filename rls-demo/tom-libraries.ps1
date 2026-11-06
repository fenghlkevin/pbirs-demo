Get-ChildItem 'C:\Program Files\Microsoft SQL Server','C:\Program Files\Microsoft SQL Server Management Studio 22' -Filter Microsoft.AnalysisServices.Tabular.dll -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName
Get-ChildItem 'E:\PowerDestop\bin\AnalysisServices' | Select-Object -First 15 -ExpandProperty Name
