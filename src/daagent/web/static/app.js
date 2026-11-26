const $ = (id) => document.getElementById(id);
let currentSession = null;
let traceBox = null;
let stepCount = 0;

$('new-session').onclick = () => {
  currentSession = 'session-' + Date.now();
  $('messages').innerHTML = '';
  loadSessions();
};

async function send() {
  const input = $('input');
  const q = input.value.trim();
  if (!q) return;
  input.value = '';
  addMessage('user', q);
  if (!currentSession) currentSession = 'session-' + Date.now();
  $('progress').textContent = '处理中…';
  $('send').disabled = true;

  // 默认折叠的「已完成」思考块
  stepCount = 0;
  traceBox = document.createElement('details');
  traceBox.className = 'trace-box';
  const summary = document.createElement('summary');
  summary.textContent = '⏳ 思考中…';
  traceBox.appendChild(summary);
  const body = document.createElement('div');
  body.className = 'trace-body';
  traceBox.appendChild(body);
  $('messages').appendChild(traceBox);
  scroll();

  const payload = {
    question: q,
    model: $('model-select').value,
    session_id: currentSession,
    deep_thinking: $('deep-thinking').checked,
  };
  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        handleEvent(JSON.parse(line.slice(6)));
      }
    }
  } catch (e) {
    addMessage('agent', '出错了：' + e.message);
    $('progress').textContent = '失败';
  } finally {
    $('send').disabled = false;
    loadSessions();
  }
}

function handleEvent(e) {
  if (e.type === 'thought') {
    appendTrace('💭 ' + e.content);
  } else if (e.type === 'tool_call') {
    stepCount++;
    appendTrace('⚙ ' + e.name + ' ' + JSON.stringify(e.args).slice(0, 80));
  } else if (e.type === 'tool_result') {
    appendTrace('👁 ' + e.result.slice(0, 160), 'obs');
  } else if (e.type === 'done') {
    finishTrace();
    addMessage('agent', e.answer);
    $('token-usage').textContent = `${e.tokens} tokens · ${e.llm_calls} 次 LLM`;
    $('progress').textContent = '完成';
  } else if (e.type === 'error') {
    finishTrace();
    addMessage('agent', '出错了：' + e.message);
    $('progress').textContent = '失败';
  }
}

function appendTrace(text, cls) {
  if (!traceBox) return;
  const box = traceBox.querySelector('.trace-body');
  const div = document.createElement('div');
  div.className = 'trace-line ' + (cls || '');
  div.textContent = text;
  box.appendChild(div);
}

function finishTrace() {
  if (!traceBox) return;
  traceBox.querySelector('summary').textContent = `✅ 已完成 · ${stepCount} 步工具调用（点击展开）`;
  // 保持折叠（不设置 open）
}

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  $('messages').appendChild(div);
  scroll();
}

/* 从已保存的事件重建折叠块（重开网页/切会话时用） */
function renderTraceBlock(events) {
  const steps = events.filter((e) => e.type === 'tool_call').length;
  const details = document.createElement('details');
  details.className = 'trace-box';
  const summary = document.createElement('summary');
  summary.textContent = `✅ 已完成 · ${steps} 步工具调用（点击展开）`;
  details.appendChild(summary);
  const body = document.createElement('div');
  body.className = 'trace-body';
  events.forEach((e) => {
    let text = '';
    if (e.type === 'thought') text = '💭 ' + e.content;
    else if (e.type === 'tool_call') text = '⚙ ' + e.name + ' ' + JSON.stringify(e.args).slice(0, 80);
    else if (e.type === 'tool_result') text = '👁 ' + (e.result || '').slice(0, 160);
    if (text) {
      const div = document.createElement('div');
      div.className = 'trace-line';
      div.textContent = text;
      body.appendChild(div);
    }
  });
  details.appendChild(body);
  $('messages').appendChild(details);
  scroll();
}

function scroll() { $('messages').scrollTop = $('messages').scrollHeight; }

/* 会话列表（可切换） */
async function loadSessions() {
  const res = await fetch('/api/sessions');
  const d = await res.json();
  const list = $('session-list');
  list.innerHTML = '';
  d.sessions.forEach((s) => {
    const li = document.createElement('li');
    li.textContent = (s.first_question || '会话').slice(0, 18);
    li.classList.toggle('current', s.session_id === currentSession);
    li.onclick = () => switchSession(s.session_id);
    list.appendChild(li);
  });
}

async function switchSession(sid) {
  currentSession = sid;
  const res = await fetch('/api/sessions/' + sid);
  const d = await res.json();
  $('messages').innerHTML = '';
  d.messages.forEach((m) => {
    if (m.role === 'user') {
      addMessage('user', m.content);
    } else {
      if (m.trace && m.trace.length) renderTraceBlock(m.trace);
      addMessage('agent', m.content);
    }
  });
  loadSessions();
}

/* 工具列表（动态：harness 实际连的工具） */
async function loadTools() {
  const res = await fetch('/api/tools');
  const d = await res.json();
  const list = $('tool-list');
  list.innerHTML = '';
  d.tools.forEach((t) => {
    const li = document.createElement('li');
    li.textContent = '🔧 ' + t;
    li.dataset.tool = t;
    list.appendChild(li);
  });
}

function markTool(name) {
  const li = $('tool-list').querySelector(`[data-tool="${name}"]`);
  if (li) li.classList.add('used');
}

$('send').onclick = send;
$('input').addEventListener('keydown', (e) => { if (e.key === 'Enter') send(); });
loadSessions();
loadTools();
