from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).parent
F='/System/Library/Fonts/Supplemental/Arial.ttf'
def label(d,b,s,fill='white',color='#18304D',size=15):
 d.rectangle(b,fill=fill);d.text((b[0]+5,b[1]+3),s,fill=color,font=ImageFont.truetype(F,size))
for lang in ['en','pt']:
 # Localised explanatory overlays on actual screenshots; data visualisations are retained.
 im=Image.open(R.parent/'video-zh/assets/portal.png').convert('RGB');d=ImageDraw.Draw(im)
 label(d,(220,4,310,40),'Home' if lang=='en' else 'Início','#282828','white')
 label(d,(1481,8,1640,37),'Search' if lang=='en' else 'Pesquisar','#BBB','#333')
 label(d,(0,49,240,90),'Favourites     Browse' if lang=='en' else 'Favoritos     Procurar')
 label(d,(1715,49,1919,89),'Publish       Tiles' if lang=='en' else 'Publicar       Mosaicos')
 label(d,(0,93,180,125),'Folders (3)' if lang=='en' else 'Pastas (3)')
 im.save(R/lang/'assets/portal.png')
 im=Image.open(R.parent/'video-zh/assets/report.png').convert('RGB');d=ImageDraw.Draw(im)
 for x,s in [(33,'Name' if lang=='en' else 'Nome'),(342,'Type' if lang=='en' else 'Tipo'),(775,'Path' if lang=='en' else 'Caminho'),(1534,'Actions' if lang=='en' else 'Acções')]:label(d,(x,0,x+180,32),s,'#E6EDF6',size=15)
 label(d,(1539,52,1620,89),'Open' if lang=='en' else 'Abrir','#0C5194','white',14)
 label(d,(1803,140,1881,177),'Close' if lang=='en' else 'Fechar','#0C5194','white',14)
 label(d,(290,190,1595,213),'Approved benefit amount by province' if lang=='en' else 'Montante aprovado por província',size=10)
 label(d,(290,387,905,411),'Share by province' if lang=='en' else 'Distribuição por província',size=10)
 label(d,(1135,391,1195,409),'Amount' if lang=='en' else 'Montante',size=7)
 label(d,(918,631,946,644),'Total',size=7)
 label(d,(1865,246,1892,317),'',size=10)
 label(d,(65,935,137,961),'Page 1' if lang=='en' else 'Página 1',size=12)
 for y,t in [(207,'30 M'),(258,'20 M'),(308,'10 M'),(358,'0')]:label(d,(292,y,329,y+14),t,size=7)
 im.save(R/lang/'assets/report.png')
