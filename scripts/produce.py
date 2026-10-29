import argparse,csv,math,os,subprocess,re,zipfile,xml.etree.ElementTree as ET,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['Filename','Description','Keywords','Categories','Editorial','Mature content','illustration']
def read_xlsx(p):
 with zipfile.ZipFile(p) as z:
  ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   x=ET.fromstring(z.read('xl/sharedStrings.xml'))
   strings=[''.join(n.itertext()) for n in x.findall('m:si',ns)]
  x=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
  rows=[]
  for row in x.findall('.//m:sheetData/m:row',ns):
   cells={}
   for c in row.findall('m:c',ns):
    ref=c.attrib.get('r','A1');col=re.match('[A-Z]+',ref).group(); idx=0
    for a in col:idx=idx*26+ord(a)-64
    v=c.find('m:v',ns); inline=c.find('m:is',ns)
    val=v.text if v is not None else ''.join(inline.itertext()) if inline is not None else ''
    if c.attrib.get('t')=='s' and val:val=strings[int(val)]
    cells[idx-1]=val
   rows.append([cells.get(i,'') for i in range(max(cells.keys(),default=-1)+1)])
  if not rows:return []
  return [dict(zip(rows[0],r)) for r in rows[1:] if any(str(v).strip() for v in r)]
def read_input(p):
 if p.suffix.lower()=='.xlsx':return read_xlsx(p)
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def value(row,*names):
 for name in names:
  for k,v in row.items():
   if k and (k.lower().strip()==name.lower() or name.lower() in k.lower()) and str(v).strip():return str(v).strip()
 return ''
def slug(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')[:55] or 'motion'
def render(path,title,size,fps,duration):
 w,h=size; cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  for i in range(round(fps*duration)):
   t=i/(fps*duration); a=2*math.pi*t
   im=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(im)
   cx=w//2;cy=h//2;scale=min(w,h)
   # Original abstract icon-like motif; smooth periodic animation, no endpoint duplicate.
   for j in range(6):
    theta=a+j*math.pi/3
    x=cx+int(scale*.23*math.cos(theta));y=cy+int(scale*.23*math.sin(theta))
    r=int(scale*(.052+.012*math.sin(a+j)))
    d.ellipse((x-r,y-r,x+r,y+r),fill=(28,127,149),outline=(13,74,95),width=max(1,scale//200))
   r=int(scale*(.10+.015*math.cos(a)))
   d.rounded_rectangle((cx-r,cy-r,cx+r,cy+r),radius=max(4,r//4),fill=(22,70,93))
   d.ellipse((cx-r//3,cy-r//3,cx+r//3,cy+r//3),fill=(238,247,247))
   proc.stdin.write(im.tobytes())
  proc.stdin.close();err=proc.stderr.read();code=proc.wait()
  if code:raise RuntimeError(err.decode(errors='replace'))
 except Exception:
  proc.kill();raise

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',default=str(ROOT/'outputs'));ap.add_argument('--limit',type=int,default=0);ap.add_argument('--width',type=int,default=1920);ap.add_argument('--height',type=int,default=1080);ap.add_argument('--fps',type=int,default=30);ap.add_argument('--duration',type=float,default=10);ap.add_argument('--render',action='store_true');a=ap.parse_args()
 rows=read_input(Path(a.input));rows=rows[:a.limit] if a.limit else rows
 out=Path(a.output);(out/'videos').mkdir(parents=True,exist_ok=True);(out/'prompts').mkdir(exist_ok=True)
 metadata=[];manifest=[]
 for i,row in enumerate(rows,1):
  title=value(row,'Judul (Title)','title','description','kategori','category') or f'Motion {i}'
  category=value(row,'Kategori','category','categories') or 'Abstract'
  sourcekeywords=value(row,'Keywords')
  name=f'{i:03d}_{slug(title)}.mp4';p=out/'videos'/name
  prompt=f'''Create an ORIGINAL clean vector motion graphic representing: {title}. Concept category: {category}. 16:9 composition, pure white background, restrained teal/navy palette, centered visual hierarchy, precise geometry, smooth 30 fps motion, no text, no logos, no watermark, no audio. Duration {a.duration:g} seconds. Timeline: 0–2s reveal components using staggered scaling and path drawing; 2–5s establish the complete concept; 5–8s animate subtle cyclic movements and meaningful icon interactions; 8–{a.duration:g}s smoothly return all properties to their starting states. Ensure a seamless looping transition with continuous position, rotation, scale and opacity. Avoid clipping, artifacts, flicker, extra objects and unrelated elements. Note: the included basic renderer produces a generic abstract motif, NOT this semantic concept; use a custom scene renderer or an approved video model to achieve this storyboard.'''
  (out/'prompts'/(Path(name).stem+'.txt')).write_text(prompt,encoding='utf-8')
  status='PROMPT_ONLY'
  if a.render:
   try:render(p,title,(a.width,a.height),a.fps,a.duration);status='RENDERED_GENERIC_PREVIEW'
   except Exception as e:status='FAILED: '+str(e)[:180]
  kws=[s.strip() for s in sourcekeywords.split(',') if s.strip()][:35]
  if not kws:kws=[v for v in re.split(r'[^a-zA-Z]+',title.lower()) if len(v)>2][:15]+['motion graphics','animation','loop','minimal','abstract','video']
  # Never export unverified categories/flags as upload-ready.
  metadata.append({'Filename':name,'Description':f'Animated motion graphic concept of {title}. Minimal clean vector style with smooth looping movement.','Keywords':', '.join(dict.fromkeys(kws)),'Categories':'REVIEW_REQUIRED','Editorial':'no','Mature content':'no','illustration':'yes'})
  manifest.append({'filename':name,'source_title':title,'status':status,'category_review':True,'prompt':str(out/'prompts'/(Path(name).stem+'.txt'))})
 with open(out/'shutterstock_metadata_DRAFT.csv','w',encoding='utf-8-sig',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=FIELDS);wr.writeheader();wr.writerows(metadata)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'ideas':len(rows),'rendered_previews':sum(x['status']=='RENDERED_GENERIC_PREVIEW' for x in manifest),'output':str(out)},indent=2))
if __name__=='__main__':main()
