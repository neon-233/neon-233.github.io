(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  let announcementTimer;
  function announce(text) {
    const status = $('#interaction-status'); if (!status) return;
    clearTimeout(announcementTimer); status.textContent = '';
    announcementTimer = setTimeout(() => { status.textContent = text; }, 180);
  }
  const pageData = JSON.parse($('#course-data').textContent);
  const storageKey = 'jisuan-course-v6-completed';
  let completed = {};
  function readProgress() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
      completed = saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {};
    } catch (_) { /* Keep the current session usable when storage is unavailable. */ }
  }
  readProgress();
  function refreshProgress() {
    const allowed = new Set(pageData.lessons.map(x => x.key));
    const n = Object.keys(completed).filter(k => completed[k] && allowed.has(k)).length;
    $$('[data-progress-count]').forEach(e => { e.textContent = n + ' / ' + pageData.lessons.length; });
    $$('.progress-fill').forEach(e => { e.style.width = (n / pageData.lessons.length * 100) + '%'; });
    $$('[data-lesson-link]').forEach(e => e.classList.toggle('is-done', !!completed[e.dataset.lessonLink]));
    $$('input[data-complete]').forEach(e => { e.checked = !!completed[e.dataset.complete]; });
  }
  $$('input[data-complete]').forEach(e => e.addEventListener('change', () => {
    readProgress();
    completed[e.dataset.complete] = e.checked;
    try { localStorage.setItem(storageKey, JSON.stringify(completed)); }
    catch (_) { const s = $('#local-status'); if (s) s.textContent = '浏览器未允许保存，进度仅在本页会话内有效。'; }
    refreshProgress();
  }));
  refreshProgress();
  window.addEventListener('pageshow', () => { readProgress(); refreshProgress(); });
  window.addEventListener('storage', e => { if (e.key === storageKey || e.key === null) { readProgress(); refreshProgress(); } });
  const toc = $('#course-sidebar'), toggle = $('#toc-toggle');
  if (toggle && toc) {
    toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; toggle.setAttribute('aria-expanded', String(open)); toc.classList.toggle('is-open', open); });
    toc.addEventListener('click', e => { if (e.target.closest('a') && innerWidth <= 820) { toggle.setAttribute('aria-expanded', 'false'); toc.classList.remove('is-open'); } });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && toc.classList.contains('is-open')) { toc.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus(); } });
  }
  $$('.lesson-content pre').forEach(pre => {
    const shell = document.createElement('div'); shell.className = 'code-shell';
    const bar = document.createElement('div'); bar.className = 'code-bar';
    const label = document.createElement('span'); label.textContent = pre.dataset.filename || '示例 / CODE';
    const button = document.createElement('button'); button.type = 'button'; button.className = 'copy-code'; button.textContent = '复制'; button.setAttribute('aria-label', '复制 ' + label.textContent);
    const code = $('code', pre) || pre;
    button.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(code.textContent); button.textContent = '已复制'; announce(label.textContent + ' 已复制到剪贴板。'); }
      catch (_) { const selection = window.getSelection(); const range = document.createRange(); range.selectNodeContents(code); selection.removeAllRanges(); selection.addRange(range); button.textContent = '已选中，请复制'; announce(label.textContent + ' 已选中，请使用系统复制命令。'); }
      setTimeout(() => { button.textContent = '复制'; }, 2300);
    });
    bar.append(label, button); pre.before(shell); shell.append(bar, pre);
  });
  const search = $('#course-search'), results = $('#search-results');
  function runSearch() {
    const query = search.value.trim().toLocaleLowerCase(); results.replaceChildren();
    if (!query) { results.hidden = true; announce('搜索已清空。'); return; }
    results.hidden = false;
    const terms = query.split(/\s+/).filter(Boolean);
    const found = pageData.lessons.filter(x => terms.every(t => (x.title + ' ' + x.text + ' ' + x.module).toLocaleLowerCase().includes(t)));
    found.sort((a,b) => Number(b.title.toLocaleLowerCase().includes(query)) - Number(a.title.toLocaleLowerCase().includes(query)));
    const status = document.createElement('p'); status.textContent = found.length ? '找到 ' + found.length + ' 个相关章节，显示前 ' + Math.min(10,found.length) + ' 个。' : '暂未找到。可试试 ENCUT、自洽、能带、声子、NEB 或量子。';
    const list = document.createElement('ul');
    found.slice(0,10).forEach(x => { const li = document.createElement('li'), a = document.createElement('a'), title = document.createElement('strong'), detail = document.createElement('small'); a.href = x.key; title.textContent = x.title; const idx = x.text.toLocaleLowerCase().indexOf(terms[0]); detail.textContent = x.module + ' · ' + (idx > 25 ? '…' : '') + x.text.slice(Math.max(0,idx - 25),Math.max(0,idx - 25) + 110) + '…'; a.append(title,detail); li.append(a); list.append(li); });
    results.append(status,list); announce(status.textContent);
  }
  if (search && results) { search.addEventListener('input',runSearch); search.addEventListener('keydown', e => { if(e.key === 'Escape') { search.value=''; runSearch(); } }); }
  const route = $('#learning-route'), answer = $('#route-answer');
  if (route && answer) {
    const routes = {
      begin:['先建立波函数、能量和自洽的物理图像，再进入硅算例。每次练习只改变一个数值设置，保留输入与输出。','quantum-v6.html','从量子化学基础开始'],
      first:['准备获得许可的 VASP 与 PBE PAW 数据，按硅原胞范例建立四类输入。先做固定结构自洽，再测试 ENCUT 和 k 网格。','vasp-start-v6.html','进入第一份 VASP 计算'],
      bands:['先用规则 k 网格获得收敛电荷，再分别做 DOS 与高对称路径能带。磁性、DFT+U、SOC 与混合泛函需要额外处理。','vasp-electronic-v6.html','查看电子结构工作流'],
      advanced:['先确认结构、能量和力的收敛，再选择表面、缺陷、声子、NEB 或 AIMD。任务模板需要补齐体系输入并检验数值误差。','vasp-advanced-v6.html','选择进阶任务'],
      tags:['从参数的物理作用、单位和适用前提出发查找；输入审阅器仅提示常见组合问题，不能证明计算收敛。','vasp-reference-v6.html','打开参数速查']
    };
    const show = () => { const [text,href,label] = routes[route.value]; answer.replaceChildren(); const p=document.createElement('p'),a=document.createElement('a'); p.textContent=text; a.href=href;a.textContent=label+' ↗';answer.append(p,a); }; route.addEventListener('change',show);show();
  }
  let ticking = false;
  const updateReading = () => {
    const bar = $('#read-line'); const total = document.documentElement.scrollHeight - innerHeight;
    if(bar) bar.style.width = (total > 0 ? Math.min(100,scrollY/total*100) : 100)+'%';
    const lessons = $$('.lesson'); let current = lessons[0];
    lessons.forEach(s => { if(s.getBoundingClientRect().top <= 160) current=s; });
    $$('.sidebar a[href*="#"]').forEach(a => { const active = current && a.getAttribute('href') === pageData.filename+'#'+current.id; a.classList.toggle('is-active',!!active); if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current'); });
    ticking = false;
  };
  const requestReading = () => { if(!ticking) { ticking=true;requestAnimationFrame(updateReading); } };
  addEventListener('scroll',requestReading,{passive:true});addEventListener('resize',requestReading);addEventListener('load',requestReading);
  $$('details').forEach(e => e.addEventListener('toggle',requestReading));updateReading();
  const lab = $('#quantum-lab');
  if (lab) {
    lab.classList.add('lab');
    lab.innerHTML = '<h3>动手看：箱子大小怎样改变能量？</h3><p class="lab-caption">一维无限深势阱中的单电子模型；曲线由解析公式计算，不是 VASP 结果。</p><div class="lab-controls"><label for="box-length">箱长 L：<output id="length-value">1.00 nm</output><input id="box-length" type="range" min="0.5" max="3" step="0.05" value="1"></label><label for="box-n">量子数 n：<output id="n-value">1</output><input id="box-n" type="range" min="1" max="4" step="1" value="1"></label></div><svg viewBox="0 0 600 240" role="img" aria-label="一维无限深势阱波函数与概率密度曲线"><path d="M45 25V205H570M45 120H570" fill="none" stroke="#c8d7e7"/><path id="wave-path" fill="none" stroke="#285ee7" stroke-width="2.5"/><path id="density-path" fill="none" stroke="#218a88" stroke-width="2.5"/><text x="48" y="227" font-size="11" fill="#687f99">0</text><text x="550" y="227" font-size="11" fill="#687f99">x / L = 1</text><text x="49" y="18" font-size="11" fill="#285ee7">蓝：√L ψ(x)</text><text x="300" y="18" font-size="11" fill="#218a88">绿：L |ψ(x)|²</text></svg><div class="lab-results"><span>能量 <strong id="box-energy">0.376</strong> eV</span><span>内部节点 <strong id="box-nodes">0</strong> 个</span></div><p class="lab-caption">横轴 x/L 归一化为 0–1，两条曲线均以中线为零；ψ 的正负表示相位，概率密度不能为负。拖动 L 时归一化曲线不变，实际波函数振幅按 1/√L 缩放，能量按 1/L² 改变。电子质量、势阱无限深等都是这个模型的假设。</p>';
    const L = $('#box-length'), n = $('#box-n');
    function drawBox() {
      const length = Number(L.value), state = Number(n.value); $('#length-value').textContent=length.toFixed(2)+' nm'; $('#n-value').textContent=state;
      $('#box-energy').textContent=(0.3760301626167375*state*state/(length*length)).toFixed(4); $('#box-nodes').textContent=state-1;
      let wave='',density=''; for(let i=0;i<=240;i++){const x=i/240,psi=Math.SQRT2*Math.sin(state*Math.PI*x),px=45+525*x;wave+=(i?'L':'M')+px.toFixed(2)+','+(120-45*psi).toFixed(2);density+=(i?'L':'M')+px.toFixed(2)+','+(120-45*psi*psi).toFixed(2);}
      $('#wave-path').setAttribute('d',wave); $('#density-path').setAttribute('d',density);
    } L.addEventListener('input',drawBox);n.addEventListener('input',drawBox);drawBox();
  }
  const pf=$('#parameter-filter'), group=$('#parameter-group');
  if(pf && group) {
    function filterParameters(){let visible=0;const q=pf.value.trim().toLowerCase(); $$('[data-param]').forEach(row=>{const show=(!q || row.textContent.toLowerCase().includes(q)) && (!group.value || row.dataset.group===group.value);row.hidden=!show;if(show)visible++;});$('#parameter-count').textContent='显示 '+visible+' / '+$$('[data-param]').length+' 个参数';}
    pf.addEventListener('input',filterParameters);group.addEventListener('change',filterParameters);filterParameters();
  }
  const checkButton=$('#check-incar');
  if(checkButton) checkButton.addEventListener('click',()=>{
    const text=$('#incar-input').value;const values={},duplicates=[];const msgs=[];
    text.split(/\r?\n/).forEach(line=>line.split(/[#!]/)[0].split(';').forEach(segment=>{const m=segment.match(/^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);if(m){const k=m[1].toUpperCase();if(k in values)duplicates.push(k);values[k]=m[2];}}));
    const num=k=>Number((values[k]||'NaN').replace(/[dD]/g,'e'));
    const yes=k=>/^\.?T(?:RUE)?\.?$/i.test(values[k]||'');
    const msg=(type,text)=>msgs.push({type,text});
    if(!Object.keys(values).length)msg('warn','未识别到 TAG = VALUE 格式。请粘贴普通 INCAR 文本。');
    if(duplicates.length)msg('warn','有重复参数：'+[...new Set(duplicates)].join(', ')+'。请保留唯一明确设置，不依赖重复覆盖行为。');
    if(!('ENCUT' in values))msg('info','未显式设置 ENCUT。能量比较前请固定截断，并依据 POTCAR 与目标量完成收敛测试。');
    if('ENCUT' in values && !(Number.isFinite(num('ENCUT')) && num('ENCUT')>0))msg('warn','ENCUT 应为正的能量值（eV）。');
    if(num('EDIFFG')>0)msg('info','EDIFFG 为正，采用离子步能量变化判据；若想限制残余力，应核对负值的力阈值（eV/Å）。');
    if(num('EDIFF')===0)msg('info','EDIFF = 0 会按 NELM 固定迭代步数运行，不能当作通常的电子收敛停止条件。');
    if(num('ICHARG')===11)msg('info','ICHARG = 11 需要先前收敛且与结构、方法一致的 CHGCAR。此工具无法检查文件是否存在或兼容。');
    if(yes('LHFCALC') && ['FAST','VERYFAST'].includes((values.ALGO||'').toUpperCase()))msg('warn','当前混合泛函计算不应使用 ALGO=Fast 或 VeryFast；请按官方混合泛函算法说明选择求解器。');
    if(yes('LHFCALC') && num('ICHARG')===11)msg('warn','混合泛函依赖轨道构造的非局域交换，不能直接套用 PBE 的 ICHARG=11 固定电荷能带步骤。请使用对应的混合泛函工作流。');
    if([-5,-4,-14,-15].includes(num('ISMEAR')))msg('info','四面体法要有适用的规则 Γ 中心 k 网格；单 Γ 点或高对称线段路径不能直接套用这一设置。');
    if(num('ISMEAR')>0)msg('info','正 ISMEAR 对应 Methfessel–Paxton 展宽。若体系为有隙半导体或绝缘体，请重新检查展宽选择。');
    if(num('IBRION')===0 && !(num('NSW')>0))msg('warn','AIMD 需要正的 NSW；当前没有指定正的动力学步数。');
    if(num('IBRION')===0 && 'POTIM' in values && !(num('POTIM')>0))msg('warn','分子动力学时间步 POTIM 必须是正数（fs）。');
    if(num('IBRION')===0 && !('POTIM' in values))msg('warn','AIMD 必须提供正的 POTIM 时间步（fs）；此模式没有可依赖的默认时间步。应根据最快振动与能量漂移测试选择。');
    if(num('MDALGO')===3 && !('LANGEVIN_GAMMA' in values))msg('info','Langevin 动力学应核对摩擦系数 LANGEVIN_GAMMA，并与 POSCAR 元素种类数对应。');
    if(yes('LSORBIT') || yes('LNONCOLLINEAR'))msg('info','SOC / 非共线计算使用 vasp_ncl；核对 MAGMOM 的每原子三分量、SAXIS 与对称性处理。');
    if(yes('LDAU'))msg('info','DFT+U 的电荷保存/固定密度步骤需检查 LMAXMIX：d 轨道常需 4，f 轨道常需 6，并保持前后步骤一致。');
    if('NCORE' in values && 'NPAR' in values)msg('warn','同时设置了 NCORE 与 NPAR。它们控制互相关联的并行分组，请按程序版本与硬件选定一种设置。');
    if(num('IMAGES')>0 && num('POTIM')===0)msg('warn','存在 IMAGES 且 POTIM=0。原生 VASP 与 VTST 优化器的规则不同，必须确认实际使用的是哪套 NEB 实现。');
    if([3,4,5,6,7,8].includes(num('ISIF')))msg('info','此 ISIF 涉及晶胞自由度；若模型含真空或只需固定晶格，请核对是否允许这些晶胞变化。');
    if(!msgs.length)msg('info','当前文本未触发已列出的常见提示。这不表示计算设置正确、结构合理或结果已收敛。');
    const target=$('#checker-results');target.replaceChildren();const heading=document.createElement('p');heading.textContent='识别 '+Object.keys(values).length+' 个参数 · '+msgs.length+' 条提示';target.append(heading);const list=document.createElement('ul');msgs.forEach(m=>{const li=document.createElement('li');li.className=m.type;li.textContent=m.text;list.append(li);});target.append(list);target.hidden=false;announce(heading.textContent + '。请阅读下方审阅结果。');
  });
})();
