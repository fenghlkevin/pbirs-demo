Get-ChildItem E:\PowerDestop\bin -Filter '*Tabular*.dll' | Select-Object -ExpandProperty FullName
Get-ChildItem E:\PowerDestop\bin -Filter '*AnalysisServices*.dll' | Select-Object -ExpandProperty FullName
Get-ChildItem E:\PowerBI\PBIRS\ASEngine\workspaces | Select-Object Name
