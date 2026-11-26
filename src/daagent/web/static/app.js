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
  let toolCard = null;
  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, model }),
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
        const e = JSON.parse(line.slice(6));
        if (e.type === 'tool_call') {
          toolCard = addToolCard(e.name, e.args);
        } else if (e.type === 'tool_result') {
          if (toolCard) toolCard.querySelector('.tool-result').textContent = e.result.slice(0, 200);
        } else if (e.type === 'done') {
          addMessage('agent', e.answer);
          $('token-usage').textContent = `${e.tokens} tokens · ${e.llm_calls} 次 LLM 调用`;
          $('progress').textContent = '完成';
          loadSessions();
        } else if (e.type === 'error') {
          addMessage('agent', '出错了：' + e.message);
          $('progress').textContent = '失败';
        }
      }
    }
  } catch (e) {
    addMessage('agent', '出错了：' + e.message);
    $('progress').textContent = '失败';
  } finally {
    $('send').disabled = false;
  }
}

function addToolCard(name, args) {
  const div = document.createElement('div');
  div.className = 'tool-card';
  const head = document.createElement('div');
  head.className = 'tool-head';
  head.textContent = '🔧 ' + name + ' ' + JSON.stringify(args).slice(0, 80);
  const result = document.createElement('div');
  result.className = 'tool-result';
  result.textContent = '…';
  div.appendChild(head);
  div.appendChild(result);
  $('messages').appendChild(div);
  $('messages').scrollTop = $('messages').scrollHeight;
  return div;
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
