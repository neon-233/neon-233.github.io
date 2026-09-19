"""Build the self-contained V6 course pages. No network or third-party packages.

Run from the repository root: python assets/tutorial-v6/build_course.py
The five source JSON files are the editable content for this development version.
Do not rebuild a frozen/delivered version without explicit authorization.
"""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'assets/tutorial-v6'
SOURCE = ASSETS / 'source'
SPECS = [
    ('quantum', 'quantum-v6.html', '量子化学与 DFT 基础', '从波函数、能量与电子密度，建立第一性原理计算的物理图像。', ['波函数', 'Born–Oppenheimer', 'DFT', 'k 点 / PAW']),
    ('start', 'vasp-start-v6.html', '第一份 VASP 计算', '用一套硅原胞算例，学会输入文件、收敛测试、结构优化与输出检查。', ['四类输入', '硅算例', '收敛测试', '结构优化']),
    ('electronic', 'vasp-electronic-v6.html', '电子结构与物性', '从收敛电荷出发，理解能带、态密度、磁性、DFT+U 与自旋轨道耦合。', ['能带 / DOS', '磁性', 'DFT+U', 'SOC']),
    ('advanced', 'vasp-advanced-v6.html', '面向问题的进阶任务', '将基础工作流扩展到表面、缺陷、声子、反应路径与有限温度动力学。', ['表面 / 缺陷', '声子 / 弹性', 'NEB', 'AIMD / HSE']),
    ('reference', 'vasp-reference-v6.html', '参数速查与计算规范', '按作用查参数、按任务查前提，在开始计算与汇报结果前做一次自查。', ['参数索引', '输入审阅', '并行 / 重启', '可复现记录']),
    ('practice', 'practice-v6.html', '综合练习与自查', '把原理与参数组织成一份能被他人复核的计算方案、数据表和研究记录。', ['硅收敛报告', '能带与磁态', '反应路径', '采样计划']),
]

class TextOnly(HTMLParser):
    def __init__(self, markup):
        super().__init__(); self.parts=[]; self.feed(markup)
    def handle_data(self, value): self.parts.append(value)
    def text(self): return re.sub(r'\s+', ' ', ' '.join(self.parts)).strip()

def plain(markup): return TextOnly(markup).text()
def clean_title(s): return re.sub(r'^\d{1,2}\s*[·/｜]\s*', '', s).strip()
def e(s): return escape(str(s), quote=True)

def load_modules(allow_incomplete=False):
    modules=[]
    for index,(key,file,title,desc,tags) in enumerate(SPECS,1):
        path=SOURCE/(key+'.json')
        if path.exists():
            module=json.loads(path.read_text(encoding='utf-8-sig'))
            assert module['filename']==file,(path,module['filename'])
            assert module['sections'],path
        else:
            if not allow_incomplete: raise FileNotFoundError(path)
            module=dict(title=title,subtitle=desc,filename=file,kicker=f'0{index} / COURSE',estimatedMinutes=0,sections=[],sources=[],downloads=[])
        module.update(key=key,index=index,tags=tags,cardTitle=title,cardDescription=desc)
        ids=[s['id'] for s in module['sections']]
        assert len(ids)==len(set(ids)),path
        for section in module['sections']:
            assert re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',section['id']),section['id']
            section['displayTitle']=clean_title(section['title'])
        modules.append(module)
    return modules

def parameter_table(parameters):
    groups=list(dict.fromkeys(p['group'] for p in parameters))
    controls='<div class="param-controls"><label class="sr-only" for="parameter-filter">查找参数</label><input id="parameter-filter" type="search" placeholder="输入标签或用途，例如 ENCUT、温度、磁性"><label class="sr-only" for="parameter-group">参数分类</label><select id="parameter-group"><option value="">全部分类</option>'+''.join(f'<option value="{e(g)}">{e(g)}</option>' for g in groups)+'</select></div><p id="parameter-count" class="status-line" role="status"></p>'
    rows=[]
    for p in parameters:
        rows.append('<tr data-param="'+e(p['tag'])+'" data-group="'+e(p['group'])+'"><td><a href="'+e(p['url'])+'" target="_blank" rel="noopener noreferrer">'+e(p['tag'])+' ↗</a></td><td>'+e(p['group'])+'<br>'+e(p['unit'])+'</td><td><strong>'+e(p['meaning'])+'</strong><br>'+e(p['usage'])+'</td><td>'+e(p['caution'])+'</td></tr>')
    return controls+'<div class="table-wrap"><table class="parameter-table"><thead><tr><th scope="col">参数 / 官方说明</th><th scope="col">分类 / 单位</th><th scope="col">作用与使用</th><th scope="col">前提与常见误用</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'

def input_checker():
    sample='SYSTEM = review_example\nENCUT = 520\nPREC = Accurate\nEDIFF = 1E-6\nISMEAR = 0\nSIGMA = 0.05\nIBRION = 2\nISIF = 2\nNSW = 100\nEDIFFG = -0.02\n'
    return '<div class="checker"><label for="incar-input">粘贴待审阅的 INCAR（下方仅为演示片段）</label><textarea id="incar-input" spellcheck="false">'+e(sample)+'</textarea><div class="actions"><button class="button small" id="check-incar" type="button">检查常见设置问题</button></div><p class="lab-caption">全部分析在本机浏览器完成，不上传文本。仅能提示已列出的语法与参数组合问题；没有提示也不代表参数正确。不会运行 VASP，也不会读取你的计算目录。</p><div id="checker-results" class="checker-results" role="region" aria-label="输入审阅结果" hidden></div></div>'

def enhance_content(section,module):
    text=section['html']
    text=text.replace("<div id='parameter-table-slot'></div>",parameter_table(module.get('parameters',[]))).replace('<div id="parameter-table-slot"></div>',parameter_table(module.get('parameters',[])))
    text=text.replace("<div id='incar-checker-slot'></div>",input_checker()).replace('<div id="incar-checker-slot"></div>',input_checker())
    # Keep references discoverable without opening them over the current lesson.
    text=re.sub(r'<a\s+href=([\'\"])(https?://[^\'\"]+)\1(?![^>]*target=)',lambda m:'<a href='+m[1]+m[2]+m[1]+' target="_blank" rel="noopener noreferrer"',text)
    return text

def progress():
    return '<div class="progress-box"><strong>我的学习进度 <span data-progress-count>0 / 0</span></strong><div class="progress-track"><div class="progress-fill"></div></div><p id="local-status" style="margin-top:8px">勾选学完的章节；仅保存在本机浏览器。</p></div>'

def header(home=False):
    return '<a class="skip" href="#main">跳至正文</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="index-v6.html#top" aria-label="纪算，返回课题组首页"><span class="brand-mark"><span>纪</span>算</span><span class="brand-caption">计算化学学习手册<small>COMPUTATIONAL CHEMISTRY</small></span></a><nav class="top-nav" aria-label="教程导航"><a class="current" href="tutorial-v6.html#modules">课程目录</a><a class="reference-link" href="vasp-reference-v6.html">参数速查</a><a class="download-link" href="tutorial-v6.html#downloads">示例下载</a><a class="home" href="index-v6.html#top">课题组首页 ↗</a></nav></div><div id="read-line" class="read-line" aria-hidden="true"></div></header>'

def search_block():
    return '<div class="search-box" id="search"><label for="course-search">搜索全部教程</label><input type="search" id="course-search" placeholder="章节、概念或参数，例如：能带、EDIFF、声子" autocomplete="off"><span class="search-icon" aria-hidden="true">⌕</span><div id="search-results" class="search-results" hidden></div></div>'

def footer():
    return '<footer class="site-footer"><div class="wrap footer-inner"><p>纪算 · 计算化学学习手册　/　资料核对：2026.09<br>本站整理的学习资料；示例用于理解方法与工作流，参数需结合体系检验。VASP 软件与 PAW 数据须通过官方许可获取。</p><a href="tutorial-v6.html">返回教程首页 ↗</a></div></footer><a class="back-top" href="#top" aria-label="回到页面顶部">↑</a>'

def sidebar(modules,current):
    parts=['<button class="toc-button" id="toc-toggle" type="button" aria-expanded="false" aria-controls="course-sidebar">展开课程目录与学习进度 <span aria-hidden="true">＋</span></button><aside class="sidebar" id="course-sidebar" aria-label="章节目录"><p class="sidebar-title">LEARNING PATH / 学习路径</p>']
    for m in modules:
        parts.append('<details'+(' open' if m['key']==current['key'] else '')+'><summary>'+str(m['index']).zfill(2)+'　'+e(m['cardTitle'])+'</summary><ol>')
        for s in m['sections']:
            key=m['filename']+'#'+s['id']
            parts.append('<li><a data-lesson-link="'+e(key)+'" href="'+e(key)+'">'+e(s['displayTitle'])+'</a></li>')
        parts.append('</ol></details>')
    return ''.join(parts)+progress()+'</aside>'

def sources(module):
    unique={s['url']:s['title'] for s in module.get('sources',[])}
    if not unique:return ''
    return '<section class="lesson" id="sources"><div class="lesson-head"><div><h2>原始资料与延伸阅读</h2><p class="lesson-kicker">READ THE PRIMARY SOURCES</p></div></div><div class="lesson-content"><p>正文为独立整理的学习说明。标签含义和版本差异以与你的程序版本对应的官方文档为准。</p><ol class="source-list">'+''.join('<li><a target="_blank" rel="noopener noreferrer" href="'+e(url)+'">'+e(title)+'</a></li>' for url,title in unique.items())+'</ol></div></section>'

def downloadable_link(d):
    return '<a class="download-item" href="assets/tutorial-v6/examples/'+e(d['path'])+'" download><strong>'+e(d['title'])+' ↓</strong><small>'+e(d['path'])+'</small><p>'+e(d.get('description',''))+'</p></a>'

def build_module(module,modules):
    p=['<div class="wrap"><div class="breadcrumb"><a href="index-v6.html#top">课题组首页</a><span>/</span><a href="tutorial-v6.html">计算化学教程</a><span>/</span><span>'+e(module['cardTitle'])+'</span></div><div class="course-layout">',sidebar(modules,module),'<main class="article-main" id="main"><div class="article-hero"><p class="eyebrow">'+e(module['kicker'])+'</p><h1>'+e(module['title'])+'</h1><p class="lead">'+e(module['subtitle'])+'</p><div class="article-meta"><span>'+str(len(module['sections']))+' 个章节</span><span>建议分次阅读与练习</span><span>更新于 2026.09.19</span></div><p class="article-note">本手册的输入示例已按资料核对，尚未逐例完成 VASP 实算验证。使用时须结合软件版本、赝势和具体体系检验。</p></div><div style="padding-top:24px">',search_block(),'</div>']
    for i,s in enumerate(module['sections'],1):
        key=module['filename']+'#'+s['id']
        p.append('<section class="lesson" id="'+e(s['id'])+'"><div class="lesson-head"><span class="lesson-num">'+str(i).zfill(2)+'</span><div><h2>'+e(s['displayTitle'])+'</h2><p class="lesson-kicker">'+e(s.get('kicker','LEARN · PRACTICE · VERIFY'))+'</p></div></div><div class="lesson-content">'+enhance_content(s,module)+'</div><div class="lesson-complete"><label><input type="checkbox" data-complete="'+e(key)+'">我已阅读并理解本节</label><a href="#top">回到顶部 ↑</a></div></section>')
    if module.get('downloads'):
        p.append('<section class="lesson" id="module-downloads"><div class="lesson-head"><div><h2>本模块示例文件</h2><p class="lesson-kicker">DOWNLOAD & CHECK</p></div></div><div class="lesson-content"><p>先读文件说明与对应章节，再补齐模型、POTCAR 与前置计算。后缀为 .template 的文件包含待改参数，不能原样提交。</p></div><div class="downloads-grid">'+''.join(downloadable_link(d) for d in module['downloads'])+'</div></section>')
    p.append(sources(module))
    idx=modules.index(module)
    prev=modules[idx-1] if idx else None; nxt=modules[idx+1] if idx<len(modules)-1 else None
    p.append('<nav class="module-pagination" aria-label="模块切换"><a href="'+(prev['filename'] if prev else 'tutorial-v6.html')+'"><small>← 上一步</small>'+(e(prev['cardTitle']) if prev else '课程总览')+'</a><a href="'+(nxt['filename'] if nxt else 'tutorial-v6.html#downloads')+'"><small>下一步 →</small>'+(e(nxt['cardTitle']) if nxt else '下载示例，开始练习')+'</a></nav></main></div></div>')
    return ''.join(p)

def hero_art():
    return '''<div class="hero-visual" aria-label="从量子模型到材料计算的学习流程示意"><div class="visual-top"><span>A THEORY-TO-PRACTICE NOTEBOOK</span><span>01 → 06</span></div><svg class="orbital-art" viewBox="0 0 450 165" role="img" aria-label="抽象波函数与周期晶格装饰示意"><defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#b5c7df"/></pattern></defs><rect width="450" height="165" fill="url(#dots)"/><path d="M22 89H209M28 22V145" stroke="#bacbe2" fill="none"/><path d="M29 89C49 12 69 12 89 89S129 166 149 89S189 12 209 89" fill="none" stroke="#2b63d7" stroke-width="2.3"/><path d="M225 84H261M254 77 261 84 254 91" stroke="#9bafc8" fill="none"/><g stroke="#779fcd" stroke-width="1.4" fill="#ebf2fb"><path d="M290 51 343 26 398 51 345 78ZM290 51V110L345 140V78M398 51V110L345 140M290 110 343 86 398 110M343 26V86" fill="none"/><circle cx="290" cy="51" r="6"/><circle cx="343" cy="26" r="6"/><circle cx="398" cy="51" r="6"/><circle cx="345" cy="78" r="6" fill="#2a64d8"/><circle cx="290" cy="110" r="6"/><circle cx="343" cy="86" r="6" fill="#76aab6"/><circle cx="398" cy="110" r="6"/><circle cx="345" cy="140" r="6"/></g></svg><p class="visual-equation">Ĥψ = Eψ <span style="font-size:17px;color:#9daec4">→</span> ρ(r) <span style="font-size:17px;color:#9daec4">→</span> E, F, σ</p><div class="visual-steps"><span>理解物理</span><span>建立输入</span><span>验证结果</span></div><div class="code-preview"><b>PREC</b> = Accurate　　<b>EDIFF</b> = 1E-6<br># 精度设置还需要收敛测试来证明</div></div>'''

def home_content(modules,lessons,downloads):
    total_chars=sum(len(re.findall(r'[\u4e00-\u9fff]',plain(s['html']))) for m in modules for s in m['sections'])
    param_count=len(next(m for m in modules if m['key']=='reference').get('parameters',[]))
    p=['<main id="main"><section class="course-hero"><div class="wrap"><div class="breadcrumb"><a href="index-v6.html#top">课题组首页</a><span>/</span><span>计算化学教程</span></div><div class="course-hero-inner"><div><p class="eyebrow">THE JISUAN LEARNING NOTEBOOK</p><h1>从量子化学出发，<br><em>走进材料的计算世界。</em></h1><p class="lead">先理解电子与原子，再学会建立输入、执行计算与判断结果。把公式、VASP 参数和研究问题，串成一条可以亲手走完的学习路径。</p><div class="actions"><a class="button" href="quantum-v6.html">从基础开始 <span aria-hidden="true">→</span></a><a class="button secondary" href="vasp-start-v6.html">直接进入 VASP <span aria-hidden="true">↗</span></a></div><div class="hero-meta"><span>面向本科生与计算新手</span><span>中文讲解 · 原始资料链接</span></div><div class="home-progress">',progress(),'</div></div>',hero_art(),'</div></div></section><section class="section"><div class="wrap"><div class="learning-intro"><div><p class="eyebrow">A PLACE TO BEGIN</p><h2 style="margin-top:14px">带着问题学习，<br>带着证据下结论。</h2></div><div><p>本手册从量子力学与 DFT 的核心概念讲起，使用硅晶体建立入门工作流，再逐步进入电子结构、表面催化与有限温度任务。每一份参数示例都要和它的结构、赝势、前置计算以及检查方法一起阅读。</p><div class="principles"><div><b>01 / UNDERSTAND</b><h3>先问计算什么</h3><p>波函数、电子密度、能量与力，分别在回答怎样的问题。</p></div><div><b>02 / PRACTICE</b><h3>再问怎样设置</h3><p>从可读懂的输入开始，保持文件之间的单位、元素顺序与方法一致。</p></div><div><b>03 / VERIFY</b><h3>最后问是否可信</h3><p>电子收敛、数值收敛与物理结论，是需要分别验证的三件事。</p></div></div></div></div><div class="course-stats"><div class="course-stat"><strong>06</strong><span>学习模块</span></div><div class="course-stat"><strong>'+str(len(lessons)).zfill(2)+'</strong><span>详细章节</span></div><div class="course-stat"><strong>'+str(param_count)+'</strong><span>常用参数索引</span></div><div class="course-stat"><strong>'+str(len(downloads))+'</strong><span>示例与记录文件</span></div></div></div></section><section class="section soft" id="modules"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">FOLLOW THE LEARNING PATH</p><h2>一步一步，搭起计算的全貌。</h2></div><p>按顺序阅读，也可以从具体任务进入。章节内有参数解释、输入示例、检查步骤和常见误区。</p></div><div class="module-grid">']
    for m in modules:
        p.append('<a class="module-card" href="'+m['filename']+'"><div class="module-top"><span class="module-num">0'+str(m['index'])+'</span><span>'+str(len(m['sections']))+' CHAPTERS</span></div><h3>'+e(m['cardTitle'])+'</h3><p>'+e(m['cardDescription'])+'</p><div class="module-topics">'+''.join('<span>'+e(tag)+'</span>' for tag in m['tags'])+'</div><div class="card-footer"><span>进入本模块</span><span aria-hidden="true">↗</span></div></a>')
    p.append('</div></div></section><section class="section"><div class="wrap learning-intro"><div><p class="eyebrow">FIND YOUR NEXT STEP</p><h2 style="margin-top:14px">今天想先解决什么？</h2><p style="margin-top:16px">一份输入文件只是起点。选择当前目标，找到需要先了解的原理与操作。</p></div><div class="route-form"><label for="learning-route">选择学习目标</label><select id="learning-route"><option value="begin">我想从量子化学基础开始</option><option value="first">我想完成第一份 VASP 计算</option><option value="bands">我想看能带、DOS 或磁性</option><option value="advanced">我想做表面、声子、NEB 或 AIMD</option><option value="tags">我想查参数或审阅 INCAR</option></select><div class="route-answer" id="route-answer"></div></div></div></section><section class="section soft"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">SEARCH THE NOTEBOOK</p><h2>一个概念，找到它的上下文。</h2></div></div>'+search_block()+'<p class="search-hint">搜索包含全部模块的章节正文；输入多个词可进一步缩小范围。</p></div></section><section class="section" id="downloads"><div class="wrap"><div class="section-heading"><div><p class="eyebrow">FILES FOR YOUR FIRST EXPERIMENTS</p><h2>把教程带到计算目录里。</h2></div><p>下载包含输入模板和使用说明，不含 VASP 程序、POTCAR、WAVECAR 或任何真实计算结果。</p></div><a class="button" href="assets/tutorial-v6/vasp-learning-examples-v6.zip" download>下载全部示例与说明 ↓</a><p class="search-hint">先读压缩包根目录 README.md。带 .template 的文件需要替换占位符、补全结构与前置文件，不能直接提交。</p><details style="margin-top:25px"><summary>按文件查看与单独下载（'+str(len(downloads))+' 份）</summary><div class="downloads-grid">'+''.join(downloadable_link(d) for d in downloads)+'</div></details><div class="note" style="margin-top:30px"><strong>学习与使用范围</strong><p>这是一版基于官方资料整理的教学手册，输入示例尚未逐例完成 VASP 实算验证。硅入门范例、其他材料模板和解析模型演示的适用条件已分别说明；“计算结束”不能替代收敛检查。软件及赝势请使用所在课题组获得许可的版本。</p></div></div></section></main>')
    return ''.join(p),total_chars

def document(title,description,body,filename,modules,lessons):
    css=(ASSETS/'theme.css').read_text(encoding='utf-8-sig')+'\n.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}'
    js=(ASSETS/'course.js').read_text(encoding='utf-8-sig')
    data=json.dumps(dict(filename=filename,lessons=lessons),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    return '<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="'+e(description)+'"><meta name="theme-color" content="#142d4b"><title>'+e(title)+' · 纪算</title><style>'+css+'</style><noscript><style>.sidebar{display:block!important;position:static;max-height:none}.toc-button,.progress-box,.lesson-complete,.search-box,.route-form,.param-controls,#check-incar{display:none!important}</style></noscript></head><body id="top">'+header(filename=='tutorial-v6.html')+'<noscript><div class="wrap noscript-note">正文、目录链接和下载无需脚本即可阅读；搜索、代码复制、学习进度、交互模型与输入审阅需要启用 JavaScript。</div></noscript>'+body+footer()+'<div id="interaction-status" class="sr-only" role="status" aria-live="polite" aria-atomic="true"></div><script id="course-data" type="application/json">'+data+'</script><script>'+js+'</script></body></html>\n'

def write_downloads(modules):
    downloads=[d for m in modules for d in m.get('downloads',[])]
    extra=SOURCE/'extra-downloads.json'
    if extra.exists():downloads+=json.loads(extra.read_text(encoding='utf-8-sig'))
    seen=set()
    for d in downloads:
        target=ASSETS/'examples'/d['path']
        assert target.resolve().is_relative_to((ASSETS/'examples').resolve()),d['path']
        assert d['path'] not in seen,d['path'];seen.add(d['path'])
        assert target.name!='POTCAR','Licensed POTCAR data must not be distributed.'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(d['content'].rstrip()+'\n',encoding='utf-8',newline='\n')
    readme='''# 纪算 V6：VASP 学习文件

这些文件是中文教程的配套教学示例，未在本次网页开发中运行 VASP。
正式教程请从 tutorial-v6.html 开始，并阅读各文件对应章节。

## 使用前必须确认

1. 使用单位合法获得许可的 VASP 程序和 PAW 数据；压缩包不含程序、POTCAR 或真实计算结果。
2. 按 POSCAR 元素顺序准备对应 POTCAR，记录数据集版本、TITEL、ENMAX 和本地 SHA-256。
3. 硅入门输入仅针对指定原胞与 PBE 设置。所有截断能、k 网格和阈值均需检验。
4. .template 表示需要修改的模板；出现大写占位词、尖括号说明或缺少结构文件时，不可原样运行。
5. 各任务独立建目录，保留先前输入输出；按照章节复制 CHGCAR、CONTCAR 或 WAVECAR。
6. 电子收敛、离子停止、数值精度与物理可信度需要分别检查。不要把模板运行结束等同于科研结论。
7. 高级任务还要求正确的结构、边界条件、磁态和方法选择。原生 VASP 与 VTST 不能混用参数。
8. 任何作业脚本中的队列、模块名、核数与程序路径都由实际集群规定，先向管理员确认。

文件采用 UTF-8 与 LF 换行。VASP 输入格式请遵循对应官方文档；中文说明不必复制到 INCAR。

## 文件索引
'''
    readme+='\n'.join('- '+d['path']+' — '+d.get('description',d['title']) for d in downloads)+'\n'
    (ASSETS/'examples/README.md').write_text(readme,encoding='utf-8',newline='\n')
    with zipfile.ZipFile(ASSETS/'vasp-learning-examples-v6.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for filename in ['README.md']+[d['path'] for d in downloads]:
            path=ASSETS/'examples'/filename
            info=zipfile.ZipInfo('jisuan-vasp-v6/'+filename,date_time=(2026,9,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,path.read_bytes())
    return downloads

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-incomplete',action='store_true');args=parser.parse_args()
    registry=ROOT/'version-history.json'
    if registry.exists():
        frozen=json.loads(registry.read_text(encoding='utf-8-sig')).get('frozenVersions',[])
        if any(item.get('version')=='v6' for item in frozen):
            raise SystemExit('V6 已交付封存。请先复制为下一版本，不能覆盖历史页面。')
    modules=load_modules(args.allow_incomplete)
    lessons=[dict(key=m['filename']+'#'+s['id'],title=s['displayTitle'],module=m['cardTitle'],text=plain(enhance_content(s,m))) for m in modules for s in m['sections']]
    downloads=write_downloads(modules)
    home,han_count=home_content(modules,lessons,downloads)
    (ROOT/'tutorial-v6.html').write_text(document('计算化学教程', '从量子化学与 DFT 基础到 VASP 计算任务：中文讲解、输入文件、参数速查与收敛检查。',home,'tutorial-v6.html',modules,lessons),encoding='utf-8',newline='\n')
    for m in modules:
        (ROOT/m['filename']).write_text(document(m['title'],m['subtitle'],build_module(m,modules),m['filename'],modules,lessons),encoding='utf-8',newline='\n')
    sources={s['url']:s for m in modules for s in m.get('sources',[])}
    manifest=dict(version='v6',preparedOn='2026-09-19',scope='local-preview',vaspNumericalCalculationsPerformed=False,moduleCount=len(modules),lessonCount=len(lessons),chineseCharacterCount=han_count,parameterCount=len(next(m for m in modules if m['key']=='reference').get('parameters',[])),downloadCount=len(downloads),sources=list(sources.values()),pages=[dict(file=m['filename'],title=m['title'],sections=[dict(id=s['id'],title=s['displayTitle']) for s in m['sections']]) for m in modules],downloads=[{k:v for k,v in d.items() if k!='content'} for d in downloads])
    (ASSETS/'course-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['moduleCount','lessonCount','chineseCharacterCount','parameterCount','downloadCount']},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
