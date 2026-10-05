let snapshot;
async function refresh() {
  const status = document.querySelector('#mapping-status');
  const refreshButton = document.querySelector('#refresh');
  refreshButton.disabled = true;
  try {
    const response = await fetch('./api/mappings', {signal: AbortSignal.timeout(20000)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Mapping status unavailable.');
    snapshot = data;
    document.querySelector('#export').disabled = false;
    const tasks = document.querySelector('#tasks'); tasks.replaceChildren();
    status.textContent = data.tasks.length ? data.tasks.length + ' tasks saved for this source version.' : 'No tasks yet. Run the worker init or run command to seed the queue.';
    document.querySelector('#usage').textContent = 'Recent runs (tokens, not a dollar-cost estimate):\n' + data.runs.map(r => r.api_calls + ' calls · ' + r.input_tokens + ' input tokens · ' + r.output_tokens + ' output tokens · ' + r.unknown_usage_calls + ' calls with unknown usage').join('\n');
    for (const task of data.tasks) {
      const box = document.createElement('details'); box.className = 'chat-message';
      const title = document.createElement('summary'); title.textContent = task.task.key + ' — ' + task.status;
      const content = document.createElement('pre'); content.textContent = JSON.stringify({source:task.task.pages, mapping:task.mapping, flags:task.flags, error:task.error, reviewer:task.reviewer}, null, 2);
      box.append(title, content); tasks.append(box);
    }
  } catch (error) { status.textContent = error.message; }
  finally { refreshButton.disabled = false; }
}
document.querySelector('#refresh').addEventListener('click', refresh);
document.querySelector('#export').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(snapshot,null,2)],{type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = 'residential-far-mapping-drafts.json'; link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
refresh();
