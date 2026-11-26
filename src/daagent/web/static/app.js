const $ = (id) => document.getElementById(id);
let currentSession = null;
let currentModel = 'deepseek-flash';
let lastAction = null;

/* 深度思考 / 快速回答切换 */
document.querySelectorAll('#mode-toggle .mode').forEach((el) => {
  el.onclick = () => {
    document.querySelectorAll('#mode-toggle .mode').forEach((m) => m.classList.remove('active'));
    el.classList.add('active');
    currentModel = el.dataset.model;
  };
});

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
  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, model: currentModel, session_id: currentSession }),
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
  if (e.type === 'thought') addThought(e.content);
  else if (e.type === 'tool_call') { addAction(e.name, e.args); markTool(e.name); }
  else if (e.type === 'tool_result') fillObservation(e.result);
  else if (e.type === 'done') {
    addMessage('agent', e.answer);
    $('token-usage').textContent = `${e.tokens} tokens · ${e.llm_calls} 次 LLM`;
    $('progress').textContent = '完成';
  } else if (e.type === 'error') {
    addMessage('agent', '出错了：' + e.message);
    $('progress').textContent = '失败';
  }
}

/* Thought（模型的自言自语，可折叠不展示细节） */
function addThought(content) {
  const div = document.createElement('div');
  div.className = 'trace-thought';
  div.textContent = '💭 Thought: ' + content;
  $('messages').appendChild(div);
  scroll();
}

/* Action（可折叠） */
function addAction(name, args) {
  const details = document.createElement('details');
  details.className = 'trace-action';
  details.open = true;
  const summary = document.createElement('summary');
  summary.textContent = '⚙ Action: ' + name + ' ' + JSON.stringify(args).slice(0, 60);
  const obs = document.createElement('div');
  obs.className = 'observation';
  obs.textContent = '👁 Observation: …';
  details.appendChild(summary);
  details.appendChild(obs);
  $('messages').appendChild(details);
  lastAction = details;
  scroll();
}

function fillObservation(result) {
  if (lastAction) lastAction.querySelector('.observation').textContent = '👁 Observation: ' + result.slice(0, 200);
}

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  $('messages').appendChild(div);
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
  d.messages.forEach((m) => addMessage(m.role === 'user' ? 'user' : 'agent', m.content));
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
