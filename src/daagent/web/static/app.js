const $ = (id) => document.getElementById(id);

async function send() {
  const input = $('input');
  const q = input.value.trim();
  if (!q) return;
  input.value = '';
  addMessage('user', q);
  const model = $('model-select').value;
  $('progress').textContent = '处理中…';
  $('send').disabled = true;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, model }),
    });
    const data = await res.json();
    addMessage('agent', data.answer);
    $('token-usage').textContent = `${data.tokens} tokens · ${data.llm_calls} 次 LLM 调用`;
    $('progress').textContent = '完成';
    loadSessions();
  } catch (e) {
    addMessage('agent', '出错了：' + e.message);
    $('progress').textContent = '失败';
  } finally {
    $('send').disabled = false;
  }
}

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  $('messages').appendChild(div);
  $('messages').scrollTop = $('messages').scrollHeight;
}

async function loadSessions() {
  const res = await fetch('/api/sessions');
  const d = await res.json();
  const list = $('session-list');
  list.innerHTML = '';
  d.messages.slice(-10).forEach((m) => {
    const li = document.createElement('li');
    li.textContent = (m.role === 'user' ? '你：' : 'A：') + m.content.slice(0, 24);
    list.appendChild(li);
  });
}

$('send').onclick = send;
$('input').addEventListener('keydown', (e) => { if (e.key === 'Enter') send(); });
loadSessions();
