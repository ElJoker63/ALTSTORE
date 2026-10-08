// UDYAT APPS — landing
// Alimenta el iPhone del hero y el catálogo con el altstore.json real,
// y gestiona el reveal orquestado al hacer scroll.

const SOURCE_URL = 'altstore.json';
const DEEP_LINK = 'sidestore://source?url=https://sidestore.udyat.site/altstore.json';

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
}

function latestVersion(app) {
    return (app.versions && app.versions.length > 0) ? app.versions[0] : app;
}

// --- iPhone del hero: renderiza la tienda real dentro de la pantalla ---
function renderMiniStore(data) {
    const titleEl = document.getElementById('mini-title');
    const appsEl = document.getElementById('mini-apps');
    if (!titleEl || !appsEl) return;

    titleEl.textContent = data.name || 'UDYAT APPS';

    // Respeta featuredApps si existe; si no, las primeras 4 apps.
    const apps = data.apps || [];
    let featured = [];
    if (Array.isArray(data.featuredApps) && data.featuredApps.length) {
        featured = data.featuredApps
            .map((id) => apps.find((a) => a.bundleIdentifier === id))
            .filter(Boolean);
    }
    if (featured.length === 0) featured = apps.slice(0, 4);

    appsEl.innerHTML = '';
    featured.slice(0, 4).forEach((app) => {
        const row = document.createElement('div');
        row.className = 'mini-app';
        row.innerHTML = `
            ${app.iconURL ? `<img class="mini-app-icon" src="${escapeHtml(app.iconURL)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">` : '<div class="mini-app-icon"></div>'}
            <div class="mini-app-info">
                <div class="mini-app-name">${escapeHtml(app.name)}</div>
                <div class="mini-app-sub">${escapeHtml(app.subtitle || app.developerName || '')}</div>
            </div>
            <span class="mini-app-get">Obtener</span>
        `;
        appsEl.appendChild(row);
    });
}

// --- Catálogo: filas estilo App Store ---
function renderCatalog(data) {
    const list = document.getElementById('app-list');
    if (!list) return;
    const apps = data.apps || [];
    list.innerHTML = '';

    apps.forEach((app) => {
        const v = latestVersion(app);
        const meta = [app.developerName, v.version ? `v${v.version}` : null]
            .filter(Boolean).join(' · ');

        const row = document.createElement('a');
        row.className = 'app-row';
        row.href = DEEP_LINK;
        row.setAttribute('aria-label', `Instalar ${app.name} en SideStore`);
        row.innerHTML = `
            ${app.iconURL ? `<img class="app-row-icon" src="${escapeHtml(app.iconURL)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">` : '<div class="app-row-icon"></div>'}
            <div class="app-row-info">
                <div class="app-row-name">${escapeHtml(app.name)}</div>
                <div class="app-row-desc">${escapeHtml(app.localizedDescription || app.subtitle || '')}</div>
                ${meta ? `<div class="app-row-meta">${escapeHtml(meta)}</div>` : ''}
            </div>
            <span class="app-row-get">Obtener</span>
        `;
        list.appendChild(row);
    });

    if (apps.length === 0) {
        const fallback = document.getElementById('catalog-fallback');
        if (fallback) fallback.hidden = false;
    }
}

// --- Reveal orquestado ---
function initReveal() {
    const targets = document.querySelectorAll('[data-reveal]');
    if (!('IntersectionObserver' in window)) {
        targets.forEach((el) => el.classList.add('in'));
        return;
    }
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    targets.forEach((el) => observer.observe(el));
}

async function loadSource() {
    try {
        const res = await fetch(SOURCE_URL, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        renderMiniStore(data);
        renderCatalog(data);
    } catch (err) {
        console.error('No se pudo cargar la fuente:', err);
        const fallback = document.getElementById('catalog-fallback');
        if (fallback) fallback.hidden = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initReveal();
    loadSource();
});
