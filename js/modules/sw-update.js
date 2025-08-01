/**
 * SW Update Banner Utility
 * Reusable service worker update prompt for pages that don't load main.js
 */
export function setupSWUpdateBanner() {
  if (!('serviceWorker' in navigator)) return;

  function ensureBanner(registration) {
    let bar = document.getElementById('pwa-update-banner');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'pwa-update-banner';
      bar.setAttribute('role', 'status');
      bar.setAttribute('aria-live', 'polite');
      Object.assign(bar.style, {
        position: 'fixed',
        left: '0', right: '0', bottom: '0',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '10px 12px',
        background: '#0f1822',
        color: '#cfe3f7',
        borderTop: '1px solid rgba(255,255,255,0.12)',
        zIndex: '9999'
      });
      bar.innerHTML = `
        <span>Update available</span>
        <div style="margin-left:auto; display:flex; gap:8px">
          <button id="pwa-update-now" class="btn primary" style="padding:6px 10px; font-size:12px">Update now</button>
          <button id="pwa-update-later" class="btn" style="padding:6px 10px; font-size:12px">Later</button>
        </div>
      `;
      document.body.appendChild(bar);
    }
    const cleanup = () => bar?.remove();
    document.getElementById('pwa-update-later')?.addEventListener('click', cleanup);
    document.getElementById('pwa-update-now')?.addEventListener('click', () => {
      cleanup();
      if (registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    });

    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    }, { once: true });
  }

  navigator.serviceWorker.register('/sw.js').then((registration) => {
    if (registration.waiting && navigator.serviceWorker.controller) {
      ensureBanner(registration);
      return;
    }
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (!newWorker) return;
      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          ensureBanner(registration);
        }
      });
    });
    // periodic update check
    setInterval(() => registration.update().catch(() => {}), 60 * 60 * 1000);
  }).catch(() => {});
}
