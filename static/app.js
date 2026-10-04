const form = document.querySelector('#review-form');
const feedback = document.querySelector('#status');
const submit = document.querySelector('#submit');
let currentReport = '';
submit.disabled = false;
feedback.textContent = 'Review controls ready. Enter the property address and choose a PDF.';
fetch('./api/status', {signal: AbortSignal.timeout(10000)}).then(r => r.json()).then(data => {
  if (!data.analysis_available && !submit.disabled && !currentReport && feedback.textContent === 'Review controls ready. Enter the property address and choose a PDF.') feedback.textContent = 'Checklist mode: AI drawing analysis needs a server-side API key.';
}).catch(() => { feedback.textContent = 'Could not check server status.'; });
form.addEventListener('submit', async event => {
  event.preventDefault();
  const address = document.querySelector('#address');
  if (!address.value.trim()) {
    feedback.textContent = 'Enter the property address before reviewing your drawing.';
    address.focus();
    return;
  }
  const file = document.querySelector('#drawing').files[0];
  if (!file || file.size > 15 * 1024 * 1024 || !file.name.toLowerCase().endsWith('.pdf')) {
    feedback.textContent = 'Choose a PDF up to 15 MB.';
    return;
  }
  submit.disabled = true;
  document.querySelector('#result').hidden = true;
  document.querySelector('#empty').hidden = false;
  feedback.textContent = 'Reading drawing evidence and checking the resolution. Rate-limit retries are automatic; allow up to three minutes…';
  try {
    const pdf = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = () => reject(new Error('Could not read the file.'));
      reader.readAsDataURL(file);
    });
    const response = await fetch('./api/review', {signal: AbortSignal.timeout(200000), method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({address: document.querySelector('#address').value, details: document.querySelector('#details').value, filename: file.name, pdf})});
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      throw new Error('The review server is unavailable. Open the app through its running server and retry.');
    }
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Review failed.');
    currentReport = result.report;
    document.querySelector('#report').textContent = currentReport;
    document.querySelector('#report-title').textContent = result.mode === 'analysis' ? 'Preliminary report' : 'Submission checklist';
    document.querySelector('#empty').hidden = true;
    document.querySelector('#result').hidden = false;
    document.querySelector('#result').scrollIntoView({behavior: 'smooth', block: 'start'});
    feedback.textContent = result.mode === 'analysis' ? 'Review complete. Verify findings with your project team.' : 'Checklist prepared. Drawing analysis has not run.';
  } catch (error) { feedback.textContent = error.name === 'TimeoutError' ? 'The server took too long to respond. Please retry.' : error instanceof TypeError ? 'Could not connect to the review server. Check that it is running and retry.' : error.message; }
  finally { submit.disabled = false; }
});
document.querySelector('#download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([currentReport], {type: 'text/plain'}));
  const link = document.createElement('a'); link.href = url; link.download = 'nyc-zoning-review.txt'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
