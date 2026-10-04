const form = document.querySelector('#review-form');
const feedback = document.querySelector('#status');
const submit = document.querySelector('#submit');
const chatForm = document.querySelector('#chat-form');
const chatFeedback = document.querySelector('#chat-status');
const chatSend = document.querySelector('#chat-send');
let currentReport = '';
let history = [];
submit.disabled = false;
feedback.textContent = 'Review controls ready. Enter the property address and choose a PDF or image.';
fetch('./api/status', {signal: AbortSignal.timeout(10000)}).then(r => r.json()).then(data => {
  if (!data.analysis_available && !submit.disabled && !currentReport) feedback.textContent = 'Checklist mode: AI review and chat need a server-side API key.';
}).catch(() => { feedback.textContent = 'Could not check server status.'; });

async function attachmentsFrom(input, required = false) {
  const files = Array.from(input.files);
  if (required && !files.length) throw new Error('Choose a drawing PDF, photo or screenshot.');
  let pdfCount = 0, imageCount = 0, total = 0;
  const formats = {pdf: 'application/pdf', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp'};
  const result = [];
  for (const file of files) {
    const mime = formats[file.name.split('.').pop().toLowerCase()];
    if (!mime) throw new Error('Use PDF, PNG, JPEG or WebP files.');
    if (mime === 'application/pdf') pdfCount++; else imageCount++;
    total += file.size;
    if ((mime !== 'application/pdf' && file.size > 5 * 1024 * 1024) || !file.size) throw new Error('Each image must be nonempty and no larger than 5 MB.');
    if (pdfCount > 1 || imageCount > 4 || total > 15 * 1024 * 1024) throw new Error('Use one PDF and up to four images, 15 MB combined.');
    const data = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = () => reject(new Error('Could not read ' + file.name));
      reader.readAsDataURL(file);
    });
    result.push({filename: file.name, mime, data});
  }
  return result;
}

async function requestReview(path, body) {
  const response = await fetch(path, {signal: AbortSignal.timeout(200000), method: 'POST',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error('The review server is unavailable. Please sign in again and retry.');
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed.');
  return result;
}
function errorMessage(error) {
  return error.name === 'TimeoutError' ? 'The server took too long to respond. Please retry later.' : error instanceof TypeError ? 'Could not connect to the server. Please retry.' : error.message;
}
function project() {
  const address = document.querySelector('#address').value.trim();
  if (!address) { document.querySelector('#address').focus(); throw new Error('Enter the property address first.'); }
  return {address, details: document.querySelector('#details').value};
}
function busy(value) { submit.disabled = value; chatSend.disabled = value; document.querySelector('#chat-clear').disabled = value; }
function clearChat() { history = []; document.querySelector('#chat-messages').replaceChildren(); chatFeedback.textContent = ''; }
function showMessage(role, text) {
  const box = document.createElement('div'); box.className = 'chat-message ' + role;
  const title = document.createElement('strong'); title.textContent = role === 'user' ? 'YOU' : 'ZONING ASSISTANT';
  const content = document.createElement('pre'); content.textContent = text;
  box.append(title, content); document.querySelector('#chat-messages').append(box);
  const log = document.querySelector('#chat-messages'); log.scrollTop = log.scrollHeight;
}
function recentHistory() {
  let remaining = 30000; const items = [];
  for (const item of history.slice(-8).reverse()) {
    const content = item.content.slice(0, Math.min(12000, remaining));
    if (!content) break;
    items.unshift({role: item.role, content}); remaining -= content.length;
  }
  return items;
}
form.addEventListener('submit', async event => {
  event.preventDefault(); busy(true);
  try {
    const context = project(); const attachments = await attachmentsFrom(document.querySelector('#drawing'), true);
    feedback.textContent = 'Reading drawing evidence and checking references. Rate-limit retries are automatic; allow up to three minutes…';
    const result = await requestReview('./api/review', {...context, attachments});
    currentReport = result.report;
    document.querySelector('#report').textContent = currentReport;
    document.querySelector('#report-title').textContent = result.mode === 'analysis' ? 'Preliminary report' : 'Submission checklist';
    document.querySelector('#empty').hidden = true;
    document.querySelector('#result').hidden = false;
    clearChat();
    document.querySelector('#result').scrollIntoView({behavior: 'smooth', block: 'start'});
    feedback.textContent = result.mode === 'analysis' ? 'Review complete. Ask a follow-up below.' : 'Checklist prepared. AI analysis has not run.';
  } catch (error) { feedback.textContent = errorMessage(error); }
  finally { busy(false); }
});
chatForm.addEventListener('submit', async event => {
  event.preventDefault(); busy(true);
  try {
    const context = project(); const message = document.querySelector('#chat-question').value.trim();
    if (!message) throw new Error('Enter a question.');
    const attachments = await attachmentsFrom(document.querySelector('#chat-files'));
    chatFeedback.textContent = 'Checking your question against the supplied resolution. Allow up to three minutes…';
    const result = await requestReview('./api/chat', {...context, message, attachments, report: currentReport.slice(0, 24000), history: recentHistory()});
    showMessage('user', message + (attachments.length ? '\nAttached: ' + attachments.map(f => f.filename).join(', ') : ''));
    showMessage('assistant', result.report);
    history.push({role: 'user', content: message}, {role: 'assistant', content: result.report});
    document.querySelector('#chat-question').value = ''; document.querySelector('#chat-files').value = '';
    chatFeedback.textContent = result.mode === 'analysis' ? 'Answer received. Verify findings with your project team.' : 'AI chat is unavailable until an API key is configured.';
  } catch (error) { chatFeedback.textContent = errorMessage(error); }
  finally { busy(false); }
});
document.querySelector('#chat-clear').addEventListener('click', clearChat);
document.querySelector('#download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([currentReport], {type: 'text/plain'}));
  const link = document.createElement('a'); link.href = url; link.download = 'nyc-zoning-review.txt'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
