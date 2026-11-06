import sys,threading,json,unittest,requests
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from server import Handler,DemoHTTPServer
class Sample(Handler):
 def route(self):
  if self.path=='/early':return self.reply(200,{'ok':True})
  if self.path=='/body':return self.reply(200,{'body':(self.body() or b'').decode()})
  return self.reply(200,b'public-script;'*1000,'application/javascript',static=True)
class Test(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=DemoHTTPServer(('127.0.0.1',0),Sample);threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.url='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
 def test_early_post_does_not_desynchronize_connection(self):
  with requests.Session() as s:
   self.assertTrue(s.post(self.url+'/early',json={}).ok)
   r=s.post(self.url+'/body',data='new-body');self.assertEqual(r.json()['body'],'new-body')
   self.assertTrue(s.get(self.url+'/').ok)
 def test_static_compression_and_revalidation(self):
  with requests.Session() as s:
   r=s.get(self.url+'/');self.assertEqual(r.raw.version,11);self.assertEqual(r.headers['Content-Encoding'],'gzip');self.assertLess(int(r.headers['Content-Length']),len(r.content)//10)
   r=s.get(self.url+'/',headers={'If-None-Match':r.headers['ETag']});self.assertEqual(r.status_code,304);self.assertEqual(r.content,b'')
 def test_dynamic_no_store_and_opt_out(self):
  with requests.Session() as s:
   r=s.post(self.url+'/body',data='x'*3000,headers={'Accept-Encoding':'identity'});self.assertEqual(r.headers['Cache-Control'],'no-store');self.assertNotIn('Content-Encoding',r.headers)
if __name__=='__main__':unittest.main()
