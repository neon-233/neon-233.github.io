'use strict';

/* 静态发布版：数据在 data/cluster.enc.json 中用 AES-256-GCM 加密，
   密码只在浏览器本地参与 PBKDF2 派生，代码与页面都不保存明文密码。 */

const enc = (text) => new TextEncoder().encode(text);
const SVG_CIRC = 2 * Math.PI * 52;
const PHASE_ORDER = { RUNNING: 0, R: 0, PENDING: 1, Q: 1, HELD: 2, H: 2 };
const PHASE_LABEL = { running: '运行', queued: '排队', held: '挂起' };
const state = { data: null, focusUsers: [], modal: null };

function b64ToBytes(text) {
  const binary = atob(text);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function decryptPayload(password, envelope) {
  const base = await crypto.subtle.importKey('raw', enc(password), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: b64ToBytes(envelope.salt), iterations: envelope.iter, hash: 'SHA-256' },
    base,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt'],
  );
  const plain = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64ToBytes(envelope.iv) }, key, b64ToBytes(envelope.ct));
  return JSON.parse(new TextDecoder().decode(plain));
}

function el(tag, attrs, children) {
  const node = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (value !== null && value !== undefined) node.setAttribute(key, value);
    }
  }
  for (const child of children || []) {
    if (child === null || child === undefined) continue;
    node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
  }
  return node;
}

function utilColor(value, kind) {
  if (value >= 90) return '#c0392b';
  if (value >= 70) return '#c2770a';
  return kind === 'gpu' ? '#6f63c9' : '#2f8f83';
}

function ring(kind, util, big, unit, note) {
  const color = utilColor(util, kind);
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', '0 0 120 120');
  const track = document.createElementNS(svgNS, 'circle');
  track.setAttribute('class', 'track');
  track.setAttribute('cx', '60'); track.setAttribute('cy', '60'); track.setAttribute('r', '52');
  const value = document.createElementNS(svgNS, 'circle');
  value.setAttribute('class', 'value');
  value.setAttribute('cx', '60'); value.setAttribute('cy', '60'); value.setAttribute('r', '52');
  value.setAttribute('stroke', color);
  value.setAttribute('stroke-dasharray', String(SVG_CIRC.toFixed(2)));
  value.setAttribute('stroke-dashoffset', String((SVG_CIRC * (1 - Math.min(100, Math.max(0, util)) / 100)).toFixed(2)));
  svg.appendChild(track);
  svg.appendChild(value);
  return el('div', { class: 'ring' }, [
    svg,
    el('div', { class: 'ring-center' }, [
      el('b', { text: String(big) }),
      el('span', { text: unit }),
      el('small', { text: note }),
    ]),
    el('div', { class: 'ring-label', text: (util || 0).toFixed(1) + '% 占用' }),
  ]);
}

function phaseOf(jobState) {
  if (jobState === 'R' || jobState === 'RUNNING') return 'running';
  if (jobState === 'Q' || jobState === 'PENDING') return 'queued';
  if (jobState === 'H' || jobState === 'HELD' || jobState === 'SUSPENDED') return 'held';
  return 'other';
}

function card(cluster) {
  const cpu = cluster.cpu || {};
  const gpu = cluster.gpu;
  const rings = el('div', { class: 'rings' }, []);
  if (gpu && gpu.total) {
    rings.appendChild(ring('gpu', gpu.util, gpu.idle, '可用卡', '已用 ' + (gpu.total - gpu.idle) + '/' + gpu.total + ' 卡'));
  }
  rings.appendChild(ring('cpu', cpu.util, cpu.idle, '可用核', '空闲 ' + cpu.nodes_free + '/在线 ' + cpu.nodes_online + ' 台'));
  const meta = el('div', { class: 'meta' }, [
    el('div', {}, [el('b', { text: cpu.nodes_online + ' / ' + cpu.nodes_total }), '在线节点']),
    el('div', {}, [el('b', { text: String(cpu.nodes_free) }), '空闲节点']),
    el('div', {}, [el('b', { text: String(cpu.nodes_down) }), '故障节点']),
  ]);
  const parts = el('div', { class: 'parts' }, (cluster.parts || []).map((part) => {
    let text = part.name + ' ' + part.idle + '/' + part.cpus + ' 核';
    if (part.gpus) text += ' · GPU ' + part.gpus_idle + '/' + part.gpus + ' 卡';
    return el('span', { class: 'part' }, [el('b', { text: text })]);
  }));
  const counts = el('div', { class: 'counts' }, [
    el('span', { class: 'pill run' }, ['运行 ', el('b', { text: String(cluster.counts.running) })]),
    el('span', { class: 'pill queue' }, ['排队 ', el('b', { text: String(cluster.counts.queued) })]),
    el('span', { class: 'pill held' }, ['挂起 ', el('b', { text: String(cluster.counts.held) })]),
  ]);
  return el('article', {
    class: 'card clickable',
    onclick: () => openCluster(cluster.label),
  }, [
    el('div', { class: 'card-head' }, [
      el('span', { class: 'dot' }),
      el('span', { class: 'port', text: cluster.label }),
      el('span', { class: 'kind', text: cluster.scheduler }),
    ]),
    rings, meta, parts, counts,
  ]);
}

function jobTable(jobs) {
  const rows = jobs.slice(0, 200).map((job) => el('tr', {}, [
    el('td', { text: job.user }),
    el('td', { class: 'num', text: job.id }),
    el('td', {}, [el('span', { class: 'state ' + job.state, text: job.state })]),
    el('td', { class: 'num', text: job.cpus || '—' }),
    el('td', { class: 'num', text: job.elapsed || '—' }),
    el('td', { class: 'num', text: job.walltime || '—' }),
    el('td', { text: job.gres || '—' }),
    el('td', { text: job.reason || '—' }),
  ]));
  return el('div', {}, [
    el('table', {}, [
      el('thead', {}, [el('tr', {}, ['用户', '作业号', '状态', 'CPU', '已运行', '时限', 'GPU', '说明']
        .map((title) => el('th', { text: title })))]),
      el('tbody', {}, rows),
    ]),
    jobs.length > 200 ? el('p', { class: 'hint', text: '共 ' + jobs.length + ' 条，仅显示前 200 条' }) : null,
  ]);
}

function openCluster(label) {
  if (!state.data) return;
  state.focusUsers = parseNames(document.getElementById('users').value);
  state.modal = { label: label, filter: '', phase: 'all' };
  document.getElementById('modalFilter').value = '';
  document.getElementById('modal').hidden = false;
  document.body.classList.add('modal-open');
  renderModal();
}

function closeModal() {
  state.modal = null;
  document.getElementById('modal').hidden = true;
  document.body.classList.remove('modal-open');
}

function renderModal() {
  if (!state.modal) return;
  const cluster = state.data.clusters.find((item) => item.label === state.modal.label);
  if (!cluster) return;
  const focus = new Set(state.focusUsers);
  const all = cluster.jobs || [];
  const jobs = all.filter((job) => {
    if (state.modal.phase !== 'all' && phaseOf(job.state) !== state.modal.phase) return false;
    if (!state.modal.filter) return true;
    const needle = state.modal.filter.toLowerCase();
    return [job.user, job.id].some((value) => String(value || '').toLowerCase().includes(needle));
  });
  const counts = { running: 0, queued: 0, held: 0, other: 0 };
  for (const job of all) counts[phaseOf(job.state)] += 1;

  document.getElementById('modalTitle').textContent = cluster.label + ' · 全部任务';
  document.getElementById('modalSub').textContent = '运行 ' + counts.running + ' · 排队 ' + counts.queued
    + ' · 挂起 ' + counts.held + ' · 合计 ' + all.length + '　数据 ' + state.data.generated;

  const chips = document.getElementById('modalChips');
  chips.innerHTML = '';
  const options = [['all', '全部 ' + all.length]];
  for (const key of ['running', 'queued', 'held']) {
    if (counts[key]) options.push([key, PHASE_LABEL[key] + ' ' + counts[key]]);
  }
  for (const [key, text] of options) {
    chips.appendChild(el('button', {
      class: 'chip' + (state.modal.phase === key ? ' on' : ''),
      text: text,
      onclick: () => { state.modal.phase = key; renderModal(); },
    }));
  }
  if (focus.size) {
    chips.appendChild(el('span', { class: 'chip focus', text: '置顶：' + [...focus].join(', ') }));
  }

  jobs.sort((a, b) => {
    const pinA = focus.has(a.user) ? 0 : 1;
    const pinB = focus.has(b.user) ? 0 : 1;
    if (pinA !== pinB) return pinA - pinB;
    const orderA = PHASE_ORDER[a.state] === undefined ? 3 : PHASE_ORDER[a.state];
    const orderB = PHASE_ORDER[b.state] === undefined ? 3 : PHASE_ORDER[b.state];
    if (orderA !== orderB) return orderA - orderB;
    return String(a.user).localeCompare(String(b.user)) || String(a.id).localeCompare(String(b.id));
  });

  const box = document.getElementById('modalList');
  box.innerHTML = '';
  if (!jobs.length) {
    box.appendChild(el('p', { class: 'hint', text: '没有符合条件的任务' }));
    return;
  }
  box.appendChild(jobTable(jobs));
}

function parseNames(text) {
  return String(text || '').replace(/[，;；\s]+/g, ',').split(',').map((name) => name.trim()).filter(Boolean);
}

let focusTimer = null;

function syncFocus() {
  state.focusUsers = parseNames(document.getElementById('users').value);
  if (focusTimer) clearTimeout(focusTimer);
  focusTimer = setTimeout(() => { if (state.modal) renderModal(); }, 200);
  return state.focusUsers;
}

function queryUsers() {
  const names = syncFocus();
  const box = document.getElementById('userResult');
  box.innerHTML = '';
  if (!names.length) return;
  for (const name of names) {
    const jobs = [];
    const perCluster = {};
    for (const cluster of state.data.clusters) {
      const own = (cluster.jobs || []).filter((job) => job.user === name);
      if (!own.length) continue;
      const slot = { running: 0, queued: 0, held: 0 };
      for (const job of own) {
        const phase = phaseOf(job.state);
        if (slot[phase] !== undefined) slot[phase] += 1;
      }
      perCluster[cluster.label] = slot;
      for (const job of own) jobs.push({ ...job, cluster: cluster.label });
    }
    const totals = Object.values(perCluster).reduce((acc, slot) => ({
      running: acc.running + slot.running,
      queued: acc.queued + slot.queued,
      held: acc.held + slot.held,
    }), { running: 0, queued: 0, held: 0 });

    const pills = el('div', { class: 'badges' }, [
      el('span', { class: 'pill run' }, ['运行 ', el('b', { text: String(totals.running) })]),
      el('span', { class: 'pill queue' }, ['排队 ', el('b', { text: String(totals.queued) })]),
      el('span', { class: 'pill held' }, ['挂起 ', el('b', { text: String(totals.held) })]),
    ]);
    for (const [label, slot] of Object.entries(perCluster)) {
      const text = label + ' ' + slot.running + '跑/' + slot.queued + '排'
        + (slot.held ? '/' + slot.held + '挂' : '');
      pills.appendChild(el('span', { class: 'pill', text }));
    }
    const body = jobs.length
      ? jobTable(jobs)
      : el('p', { class: 'hint', text: '最近一次数据中没有该用户的任务' });
    box.appendChild(el('div', { class: 'user-card' }, [
      el('h3', {}, [name, el('span', { text: '共 ' + jobs.length + ' 条' })]),
      pills, body,
    ]));
  }
}

function render(data) {
  state.data = data;
  const grid = document.getElementById('clusters');
  grid.innerHTML = '';
  for (const cluster of data.clusters) grid.appendChild(card(cluster));
  document.getElementById('stamp').textContent = '数据时间 ' + data.generated;
  document.getElementById('foot').textContent = '每 ' + data.interval_minutes + ' 分钟自动更新';
  document.getElementById('gate').hidden = true;
  document.getElementById('app').hidden = false;
}

let envelope = null;

async function onSubmit(event) {
  event.preventDefault();
  const button = document.getElementById('gateBtn');
  const input = document.getElementById('gatePwd');
  const error = document.getElementById('gateError');
  error.hidden = true;
  button.disabled = true;
  button.textContent = '校验中…';
  try {
    const data = await decryptPayload(input.value.trim(), envelope);
    input.value = '';
    render(data);
  } catch (failure) {
    error.hidden = false;
    input.select();
    await new Promise((resolve) => setTimeout(resolve, 600));
  } finally {
    button.disabled = false;
    button.textContent = '进入';
  }
}

async function init() {
  try {
    envelope = await (await fetch('./data/cluster.enc.json', { cache: 'no-store' })).json();
  } catch (failure) {
    document.getElementById('gateHint').textContent = '数据文件加载失败，请稍后重试';
    return;
  }
  document.getElementById('gateForm').addEventListener('submit', onSubmit);
  document.getElementById('lock').addEventListener('click', () => location.reload());
  document.getElementById('users').addEventListener('input', syncFocus);
  document.getElementById('users').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') queryUsers();
  });
  document.getElementById('query').addEventListener('click', queryUsers);
  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('modalBackdrop').addEventListener('click', closeModal);
  document.getElementById('modalFilter').addEventListener('input', (event) => {
    if (!state.modal) return;
    state.modal.filter = event.target.value.trim();
    renderModal();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && state.modal) closeModal();
  });
  document.getElementById('gatePwd').focus();
}

init();
