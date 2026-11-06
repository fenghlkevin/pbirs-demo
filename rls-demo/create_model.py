import json
from pathlib import Path
rows=[['A','2026-01','A-001',100],['A','2026-02','A-002',200],['A','2026-03','A-003',300],['B','2026-01','B-001',400],['B','2026-02','B-002',500],['B','2026-03','B-003',600]]
expression='DATATABLE("Province",STRING,"Month",STRING,"Record",STRING,"Amount",INTEGER,{'+','.join('{'+','.join(json.dumps(v) for v in row)+'}' for row in rows)+'})'
columns=[{'name':name,'dataType':typ,'type':'calculatedTableColumn','sourceColumn':'['+name+']','summarizeBy':'none' if typ=='string' else 'sum'} for name,typ in [('Province','string'),('Month','string'),('Record','string'),('Amount','int64')]]
model={'name':'Model','culture':'en-US','tables':[{'name':'ProvinceSales','columns':columns,'partitions':[{'name':'DemoData','mode':'import','source':{'type':'calculated','expression':expression}}],'measures':[{'name':'VisibleAmount','expression':'SUM(ProvinceSales[Amount])','formatString':'#,0'},{'name':'VisibleRows','expression':'COUNTROWS(ProvinceSales)','formatString':'0'},{'name':'CurrentIdentity','expression':'USERNAME()'}]}], 'roles':[{'name':'Province_'+p,'annotations':[{'name':'PBI_Id','value':{'A':'de8f6c4d-cd64-4d01-a145-fe8e4877a396','B':'64df9c65-8cd8-4383-af9e-1ac1a1f271f4'}[p]}],'modelPermission':'read','tablePermissions':[{'name':'ProvinceSales','filterExpression':'[Province] = "'+p+'"'}]} for p in ['A','B']]}
request={'create':{'database':{'id':'P4_RLS_Demo_Build','name':'P4_RLS_Demo_Build','compatibilityLevel':1565,'model':model}}}
Path('rls-demo/create-model.json').write_text(json.dumps(request,ensure_ascii=False))
