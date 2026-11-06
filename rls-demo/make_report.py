import json,zipfile,secrets,copy
from pathlib import Path
base=zipfile.ZipFile('rls-demo/base.pbix');layout=json.loads(base.read('Report/Layout').decode('utf-16-le'))
encode=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':'))
visuals=[]
def visual(kind,x,y,w,h,selects,projections):
 query={'Version':2,'From':[{'Name':'p','Entity':'ProvinceSales','Type':0}],'Select':selects}
 config={'name':secrets.token_hex(10),'layouts':[{'id':0,'position':{'x':x,'y':y,'width':w,'height':h,'z':len(visuals),'tabOrder':len(visuals)}}], 'singleVisual':{'visualType':kind,'projections':projections,'prototypeQuery':query,'drillFilterOtherVisuals':True}}
 binding={'Primary':{'Groupings':[{'Projections':list(range(len(selects))),'Subtotal':1}]},'DataReduction':{'DataVolume':3,'Primary':{'Window':{'Count':500}}},'Version':1}
 obj={'x':x,'y':y,'z':len(visuals),'width':w,'height':h,'config':encode(config),'filters':'[]','query':encode({'Commands':[{'SemanticQueryDataShapeCommand':{'Query':query,'Binding':binding,'ExecutionMetricsKind':1}}]}),'tabOrder':len(visuals)}
 visuals.append(obj);return obj
def column(name):return {'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':name},'Name':'ProvinceSales.'+name,'NativeReferenceName':name}
def measure(name):return {'Measure':{'Expression':{'SourceRef':{'Source':'p'}},'Property':name},'Name':'ProvinceSales.'+name,'NativeReferenceName':name}
def agg(name):return {'Aggregation':{'Expression':{'Column':{'Expression':{'SourceRef':{'Source':'p'}},'Property':name}},'Function':0},'Name':'Sum(ProvinceSales.'+name+')','NativeReferenceName':'Amount'}
visual('clusteredColumnChart',40,145,880,340,[column('Province'),agg('Amount')],{'Category':[{'queryRef':'ProvinceSales.Province','active':True}],'Y':[{'queryRef':'Sum(ProvinceSales.Amount)'}]})
for name,x,y,w,h in [('VisibleAmount',1000,145,400,160),('VisibleRows',1450,145,400,160),('CurrentIdentity',1000,340,850,140)]:
 visual('card',x,y,w,h,[measure(name)],{'Values':[{'queryRef':'ProvinceSales.'+name}]})
select=[column('Province'),column('Month'),column('Record'),agg('Amount')]
visual('tableEx',40,550,1810,450,select,{'Values':[{'queryRef':s['Name']} for s in select]})
textconfig={'name':secrets.token_hex(10),'layouts':[{'id':0,'position':{'x':40,'y':20,'width':1800,'height':90,'z':10,'tabOrder':10}}], 'singleVisual':{'visualType':'textbox','objects':{'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':'P6 行级权限验证：省份缴费分析','textStyle':{'fontSize':'30pt','fontFamily':'Segoe UI','fontWeight':'bold'}}]}]}}]}}}
visuals.append({'x':40,'y':20,'width':1800,'height':90,'z':10,'config':encode(textconfig),'filters':'[]','tabOrder':10})
section=layout['sections'][0];section.update(displayName='省份数据与当前身份',visualContainers=visuals)
Path('rls-demo/report-layout.json').write_text(encode(layout))
def package(model):
 with zipfile.ZipFile('rls-demo/Province_RLS_Demo.pbix','w',zipfile.ZIP_DEFLATED) as z:
  for name in base.namelist():
   if name in ('DataModel','SecurityBindings','DiagramLayout'):continue
   data=base.read(name)
   if name=='Report/Layout':data=encode(layout).encode('utf-16-le')
   if name=='[Content_Types].xml':
    data=data.replace(b'<Override PartName="/SecurityBindings" ContentType="" />',b'')
   z.writestr(name,data)
  z.writestr('DataModel',Path(model).read_bytes())
if __name__=='__main__':
 import sys
 if len(sys.argv)>1:package(sys.argv[1]);print('Report packaged')
