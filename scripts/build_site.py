"""Stage only the dashboard and reader documentation for GitHub Pages."""
from pathlib import Path
from shutil import copytree,copy2
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
site=ROOT/'_site';site.mkdir(exist_ok=True)
copytree(ROOT/'dashboard',site/'dashboard',dirs_exist_ok=True)
(site/'docs').mkdir(exist_ok=True)
for ext in ('*.html','*.md'):
    for file in (ROOT/'docs').glob(ext):copy2(file,site/'docs'/file.name)
copytree(ROOT/'docs/screenshots',site/'docs/screenshots',dirs_exist_ok=True)
(site/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=dashboard/"><title>Calgary 311 Service Operations</title><body><a href="dashboard/">Open Calgary 311 Service Operations</a></body></html>\n',encoding='utf-8')
(site/'.nojekyll').touch()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v and not v.startswith(('https:','http:','#','data:')):self.links.append(v.split('#')[0])
for file in site.rglob('*.html'):
    parser=Links();parser.feed(file.read_text(encoding='utf-8'))
    for link in parser.links:assert (file.parent/link).exists(),(file,link)
print('Site staged; all local HTML links resolve.')
