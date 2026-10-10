const status = document.querySelector('#status');
const disconnect = document.querySelector('#disconnect');
async function refresh() {
  try {
    const response = await fetch('/api/onedrive/status', {signal:AbortSignal.timeout(20000)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Connection unavailable.');
    status.textContent = body.connected ? 'OneDrive connection saved. Destination: '+body.folder : 'OneDrive is not connected yet.';
    disconnect.disabled = !body.connected;
  } catch (error) { status.textContent = error.message; }
}
disconnect.addEventListener('click', async () => {
  disconnect.disabled = true;
  try {
    const response = await fetch('/api/onedrive/disconnect', {method:'POST',signal:AbortSignal.timeout(20000)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Disconnect failed.');
    await refresh();
  } catch (error) { status.textContent = error.message; disconnect.disabled = false; }
});
refresh();
