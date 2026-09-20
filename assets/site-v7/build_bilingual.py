"""Build the standalone Chinese/English V7 site from frozen V7 templates.

Translations are build-time data. The deployed site never calls a translation API.
Run: python assets/site-v7/build_bilingual.py --collect
Then fill translations/en.json and run without --collect.
"""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
from urllib.parse import urlsplit
import argparse
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
COURSE = ROOT / 'assets/tutorial-v7'
HAN = re.compile(r'[\u3400-\u9fff]')
REQUIRED = set()
MISSING = set()
CATALOG = {}
COLLECT = False
FILES = sorted(p.name for p in (BASE / 'templates').glob('*.html'))
EN_NAMES = {name: name.replace('-v7.html', '-v7-en.html') for name in FILES}
JS_TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`')
ATTR_TEXT = {'alt', 'title', 'aria-label', 'placeholder', 'content', 'data-filename', 'data-group', 'value'}
SKIP_JSON_KEYS = {'key', 'filename', 'text'}

def tr(value):
    if not HAN.search(value): return value
    stripped = value.strip()
    if not stripped: return value
    REQUIRED.add(stripped)
    if COLLECT: return value
    if stripped not in CATALOG:
        MISSING.add(stripped)
        return value
    out = CATALOG[stripped]
    if not isinstance(out, str) or (not out.strip() and stripped != '个') or HAN.search(out):
        raise ValueError('Invalid English translation: ' + stripped[:80])
    left = value[:len(value) - len(value.lstrip())]
    right = value[len(value.rstrip()):]
    return left + out + right

def prose_lines(value):
    return '\n'.join(tr(line) for line in value.split('\n'))

def code_text(value):
    """Only translate Chinese comments or documentary lines; retain code verbatim."""
    output = []
    for line in value.splitlines(keepends=True):
        if not HAN.search(line):
            output.append(line); continue
        content = line.rstrip('\r\n'); ending = line[len(content):]
        # The course's executable examples use English identifiers and values.
        if '#' in content:
            before, comment = content.split('#', 1)
            output.append(before + '#' + tr(comment) + ending)
        elif re.match(r'^\s*(//|!)(?![=])', content):
            m = re.match(r'^(\s*(?://|!)\s*)(.*)$', content)
            output.append(m[1] + tr(m[2]) + ending)
        else:
            # Blank research-record forms and explicit placeholder labels.
            output.append(tr(content) + ending)
    return ''.join(output)

def english_url(value):
    if urlsplit(value).scheme or value.startswith('//'): return value
    for zh, en in EN_NAMES.items(): value = value.replace(zh, en)
    value = value.replace('assets/tutorial-v7/examples/', 'assets/tutorial-v7/examples-en/')
    value = value.replace('vasp-learning-examples-v7.zip', 'vasp-learning-examples-v7-en.zip')
    return value

def decode_js_string(token):
    quote = token[0]
    if quote == '"':
        try: return json.loads(token)
        except json.JSONDecodeError: pass
    value = token[1:-1]
    escapes = {'n':'\n', 'r':'\r', 't':'\t', 'b':'\b', 'f':'\f', 'v':'\v', '0':'\0'}
    def replacement(m):
        x = m[1]
        if x.startswith('u') and len(x)==5: return chr(int(x[1:], 16))
        if x.startswith('x') and len(x)==3: return chr(int(x[1:], 16))
        return escapes.get(x, x)
    return re.sub(r'\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)', replacement, value)

def english_js(script):
    def convert(m):
        token = m[0]
        if token.startswith('//') or token.startswith('/*'): return token
        if not HAN.search(token):
            # Script-generated navigation links must remain within English pages.
            value = english_url(token)
            return value
        if token[0] == '`' and '${' in token:
            raise ValueError('A Chinese interpolated template needs explicit translation')
        value = decode_js_string(token)
        if re.search(r'<[A-Za-z][^>]*>', value): value = html_transform(value, True)
        else: value = tr(value)
        return json.dumps(value, ensure_ascii=False)
    return JS_TOKEN.sub(convert, script)

def progress_patch(script):
    # Both languages share completion IDs; navigation/search URLs stay localized.
    if "jisuan-course-v7-completed" not in script: return script
    script = script.replace("  let completed = {};", "  const lessonId = key => key.replace('-v7-en.html', '-v7.html');\n  let completed = {};")
    script = script.replace('pageData.lessons.map(x => x.key)', 'pageData.lessons.map(x => lessonId(x.key))')
    script = script.replace('allowed.has(k)', 'allowed.has(lessonId(k))')
    script = script.replace('completed[e.dataset.lessonLink]', 'completed[lessonId(e.dataset.lessonLink)]')
    script = script.replace('completed[e.dataset.complete]', 'completed[lessonId(e.dataset.complete)]')
    # Canonicalize values from either language before saving.
    return script

def json_translate(value, key=None):
    if isinstance(value, list): return [json_translate(x) for x in value]
    if isinstance(value, dict): return {k:json_translate(v,k) for k,v in value.items()}
    if isinstance(value, str):
        if key == 'text': return value # Rebuilt from translated lesson DOM below.
        if key in ('key', 'filename'): return english_url(value)
        return tr(value)
    return value

class Transform(HTMLParser):
    def __init__(self, en):
        super().__init__(convert_charrefs=False)
        self.en=en; self.out=[]; self.in_script=False;self.script_type='';self.in_style=False;self.pre=0
    def handle_starttag(self, tag, attrs):
        original=self.get_starttag_text()
        if tag == 'script':
            self.in_script=True; self.script_type=dict(attrs).get('type','')
        if tag == 'style': self.in_style=True
        if tag == 'pre': self.pre+=1
        if not self.en:
            self.out.append(original);return
        result=[]
        for key,value in attrs:
            if value is None: result.append(key);continue
            if key in ATTR_TEXT and HAN.search(value): value=tr(value)
            if key in ('href','src','action'): value=english_url(value)
            if key == 'lang' and tag=='html': value='en'
            if key == 'data-lesson-link' or key=='data-complete':
                # IDs intentionally stay in the Chinese canonical form.
                pass
            result.append(key+'="'+escape(value,quote=True)+'"')
        self.out.append('<'+tag+(' '+' '.join(result) if result else '')+(' /' if original.endswith('/>') else '')+'>')
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag=='script':self.in_script=False
        if tag=='style':self.in_style=False
        if tag=='pre':self.pre-=1
        self.out.append('</'+tag+'>')
    def handle_data(self,data):
        if self.in_script:
            if self.script_type=='application/json':
                value=json.loads(data)
                if self.en: value=json_translate(value)
                self.out.append(json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
            else:
                script=progress_patch(data)
                self.out.append(english_js(script) if self.en else script)
        elif self.in_style: self.out.append(data)
        elif self.en:
            value=code_text(data) if self.pre else tr(unescape(data))
            if not self.pre:
                for zh,en in [('。','.'),('，',','),('；',';'),('：',':'),('（','('),('）',')'),('、',', ')]: value=value.replace(zh,en)
            if not self.pre and HAN.search(data): value=' '+value.strip()+' '
            self.out.append(escape(value,quote=False))
        else:self.out.append(data)
    def handle_entityref(self,name):self.out.append('&'+name+';')
    def handle_charref(self,name):self.out.append('&#'+name+';')
    def handle_comment(self,data):self.out.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.out.append('<!'+decl+'>')

def html_transform(text,en):
    parser=Transform(en);parser.feed(text);parser.close();return ''.join(parser.out)

SWITCH_SCRIPT = """(() => {
  document.querySelectorAll('[data-language-link]').forEach(link => {
    link.addEventListener('click', () => {
      let hash = location.hash;
      const active = document.querySelector('.sidebar a.is-active');
      if (active) hash = new URL(active.href).hash;
      else {
        const sections = [...document.querySelectorAll('main section[id]')];
        const current = sections.filter(s => s.getBoundingClientRect().top <= 125 && s.getBoundingClientRect().bottom > 125).pop();
        if (current) hash = '#' + current.id;
      }
      const destination = new URL(link.href); destination.hash = hash; link.href = destination.href;
    });
  });
})();"""

def decorate(text,name,en):
    counterpart=EN_NAMES[name]
    label='Language' if en else '语言切换'
    switch='<div class="language-switch" role="group" aria-label="'+label+'"><a href="'+name+'" lang="zh-CN" hreflang="zh-CN" data-language-link="zh"'+('' if en else ' aria-current="page"')+'>中文</a><a href="'+counterpart+'" lang="en" hreflang="en" data-language-link="en"'+(' aria-current="page"' if en else '')+'>EN</a></div>'
    # Existing header nav is followed by its flex container closing tag.
    end=text.find('</nav>',text.find('<header'))+len('</nav>')
    assert end>=len('</nav>')
    text=text[:end]+switch+text[end:]
    zhurl='https://jisuan.bond/'+('' if name=='index-v7.html' else name)
    enurl='https://jisuan.bond/'+counterpart
    head='<link rel="alternate" hreflang="zh-CN" href="'+zhurl+'"><link rel="alternate" hreflang="en" href="'+enurl+'"><link rel="alternate" hreflang="x-default" href="'+zhurl+'"><link rel="canonical" href="'+(enurl if en else zhurl)+'">'
    css=(BASE/'bilingual.css').read_text(encoding='utf-8')
    text=text.replace('</head>',head+'<style>'+css+'</style></head>',1)
    text=text.replace('</body>','<script>'+SWITCH_SCRIPT+'</script></body>',1)
    if en:
        # Brand word is split into two elements in the original Chinese logo.
        text=re.sub(r'<span class="brand-mark">\s*<span>.*?</span>\s*.*?</span>', '<span class="brand-mark"><span>Ji</span>suan</span>',text,count=1,flags=re.S)
        # Short labels fit the desktop navigation; full headings remain descriptive.
        text=re.sub(r'(<a href="#intro">)\s*About the Group\s*(</a>)',r'\1About\2',text)
        text=re.sub(r'(<a href="#resume">)\s*Principal Investigator\s*(</a>)',r'\1PI\2',text)
        text=re.sub(r'(<a href="tutorial-v7-en.html">)\s*Computational Chemistry Tutorials\s*(</a>)',r'\1Tutorials\2',text)
        if name == 'index-v7.html':
            text=re.sub(r'<h1 id="hero-title">.*?</h1>', '<h1 id="hero-title">Atomic insights.<br><span>Materials possibilities.</span></h1>',text,count=1,flags=re.S)
        # Do not repeat the group name in two languages inside the English logo.
        text=re.sub(r'(<span class="brand-caption">)\s*Yujin Ji Research Group\s*<small>YUJIN JI RESEARCH GROUP</small>',r'\1Yujin Ji Research Group<small>FUNSOM · SOOCHOW UNIVERSITY</small>',text)
    return text

class LessonText(HTMLParser):
    def __init__(self):
        super().__init__();self.sections={};self.section=None;self.depth=0;self.parts=[];self.skip=0
    def handle_starttag(self,t,attrs):
        d=dict(attrs)
        if t=='section' and 'lesson' in d.get('class','').split() and d.get('id'):
            self.section=d['id'];self.depth=1;self.parts=[]
        elif self.section and t=='section':self.depth+=1
        if t in ('style','script'):self.skip+=1
    def handle_endtag(self,t):
        if t in ('style','script'):self.skip-=1
        if self.section and t=='section':
            self.depth-=1
            if self.depth==0:
                self.sections[self.section]=re.sub(r'\s+',' ',' '.join(self.parts)).strip();self.section=None
    def handle_data(self,s):
        if self.section and not self.skip:self.parts.append(s)

def rebuild_search(pages):
    extracted={}
    for name,text in pages.items():
        if not name.endswith('-en.html'):continue
        p=LessonText();p.feed(text);extracted[name]=p.sections
    pattern=re.compile(r'(<script id="course-data" type="application/json">)(.*?)(</script>)',re.S)
    for name,text in list(pages.items()):
        if not name.endswith('-en.html'):continue
        def update(m):
            data=json.loads(m[2])
            for lesson in data['lessons']:
                file,anchor=lesson['key'].split('#',1)
                lesson['text']=extracted[file][anchor]
            return m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m[3]
        pages[name]=pattern.sub(update,text)

def process_downloads(write):
    translated={}
    for file in sorted((COURSE/'examples').rglob('*')):
        if not file.is_file():continue
        rel=file.relative_to(COURSE/'examples').as_posix()
        text=file.read_text(encoding='utf-8-sig')
        if file.suffix in ('.md','.txt') or rel.endswith('.md.template'):
            result=prose_lines(text)
        else:result=code_text(text)
        result=english_url(result)
        translated[rel]=result
        if write:
            output=COURSE/'examples-en'/rel;output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(result,encoding='utf-8',newline='\n')
    return translated

def write_zip(folder,path):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in sorted(folder.rglob('*')):
            if not file.is_file():continue
            info=zipfile.ZipInfo(file.relative_to(folder).as_posix(),date_time=(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,file.read_bytes())

def main():
    global COLLECT,CATALOG
    parser=argparse.ArgumentParser();parser.add_argument('--collect',action='store_true');args=parser.parse_args();COLLECT=args.collect
    registry=json.loads((ROOT/'version-history.json').read_text(encoding='utf-8'))
    if any(x.get('version')=='v7' for x in registry['frozenVersions']): raise SystemExit('V7 is frozen; create a new version before editing.')
    mapping=BASE/'translations/en.json'
    if mapping.exists():CATALOG=json.loads(mapping.read_text(encoding='utf-8'))
    overrides=BASE/'translations/overrides.json'
    if overrides.exists():CATALOG.update(json.loads(overrides.read_text(encoding='utf-8')))
    headings=BASE/'translations/headings.json'
    if headings.exists():CATALOG.update(json.loads(headings.read_text(encoding='utf-8')))
    interface=BASE/'translations/interface.json'
    if interface.exists():CATALOG.update(json.loads(interface.read_text(encoding='utf-8')))
    parameters=BASE/'translations/parameters-en.json'
    if parameters.exists():
        param_text=json.loads(parameters.read_text(encoding='utf-8'))
        source=(BASE/'templates/vasp-reference-v7.html').read_text(encoding='utf-8')
        rows=re.findall(r'<tr data-param="([^"]+)"[^>]*>(.*?)</tr>',source,re.S)
        assert len(rows)==60 and set(param_text)=={tag for tag,_ in rows}
        for tag,row in rows:
            fields=re.search(r'<strong>(.*?)</strong><br>(.*?)</td><td>(.*?)</td>',row,re.S)
            assert fields,tag
            for zh,en in zip(fields.groups(),param_text[tag]): CATALOG[unescape(zh).strip()]=en
    pages={}
    for name in FILES:
        template=(BASE/'templates'/name).read_text(encoding='utf-8')
        pages[name]=decorate(html_transform(template,False),name,False) if not COLLECT else template
        pages[EN_NAMES[name]]=decorate(html_transform(template,True),name,True) if not COLLECT else html_transform(template,True)
    downloads=process_downloads(False)
    if COLLECT:
        values=sorted(REQUIRED)
        (BASE/'translations/segments.json').write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'segments':len(values),'characters':sum(map(len,values))}));return
    if MISSING:
        (BASE/'translations/missing.json').write_text(json.dumps(sorted(MISSING),ensure_ascii=False,indent=2),encoding='utf-8')
        raise SystemExit(f'{len(MISSING)} translations are missing; nothing published.')
    rebuild_search(pages)
    for name,text in pages.items():(ROOT/name).write_text(text,encoding='utf-8',newline='\n')
    process_downloads(True)
    write_zip(COURSE/'examples',COURSE/'vasp-learning-examples-v7.zip')
    write_zip(COURSE/'examples-en',COURSE/'vasp-learning-examples-v7-en.zip')
    manifest={'version':'v7','defaultLanguage':'zh-CN','languages':['zh-CN','en'],'pages':[{'zh':n,'en':EN_NAMES[n]} for n in FILES],'translatedSegments':len(REQUIRED),'downloadFilesPerLanguage':len(downloads),'translationRuntimeNetworkRequests':False,'sourceVersion':'v6'}
    (BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pages':len(pages),'translationSegments':len(REQUIRED),'downloadFilesPerLanguage':len(downloads)}))

if __name__=='__main__': main()
