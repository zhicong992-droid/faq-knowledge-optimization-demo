const $ = (selector) => document.querySelector(selector);

async function loadHealth() {
  const response = await fetch('/api/health');
  const data = await response.json();
  $('#metrics').innerHTML = `
    <div class="metric"><span>FAQ 数量</span><strong>${data.metrics.faq_count}</strong><small>演示知识库</small></div>
    <div class="metric"><span>问法覆盖</span><strong>${Math.round(data.metrics.coverage_before * 100)}%</strong><small>优化前基线</small></div>
    <div class="metric"><span>健康问题</span><strong>${data.finding_count}</strong><small>待治理发现</small></div>`;
}

$('#search-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const query = $('#query').value;
  const data = await (await fetch('/api/search', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query})})).json();
  $('#search-results').classList.remove('empty');
  $('#search-results').innerHTML = data.hits.length ? data.hits.map((hit, index) => `
    <article class="result"><div class="rank">0${index + 1}</div><div><b>${hit.question}</b><p>${hit.category} · ${hit.channels.join(' + ')} · ${hit.score.toFixed(4)}</p></div></article>`).join('') : '没有召回结果';
});

$('#run-agent').addEventListener('click', async () => {
  const button = $('#run-agent');
  button.disabled = true;
  button.textContent = '运行中...';
  const data = await (await fetch('/api/agent/run', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({badcases: [{query: '忘记密码怎么改？', expected_faq_id: 'faq-001', reason: '线上低置信度'}]})})).json();
  $('#agent-output').classList.remove('empty');
  $('#agent-output').innerHTML = `${data.steps.map(step => `<div class="step"><span class="check">✓</span><span>${step.name}</span><small>${step.detail}</small></div>`).join('')}<div class="summary"><b>${data.actions.length}</b> 个可自动执行动作 · <b>${data.pending_review.length}</b> 个待审核动作</div>`;
  button.disabled = false;
  button.textContent = '再次运行运营 Agent';
});

loadHealth();
