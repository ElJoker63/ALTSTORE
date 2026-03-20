// Load apps and news from altstore.json
async function loadAltStoreData() {
    try {
        const response = await fetch('altstore.json');
        const data = await response.json();
        
        // Load apps
        loadApps(data.apps);
        
        // Load news
        loadNews(data.news);
    } catch (error) {
        console.error('Error loading altstore data:', error);
    }
}

// Load apps
function loadApps(apps) {
    const container = document.getElementById('apps-container');
    
    if (apps && apps.length > 0) {
        // Crear contenedor interno para las cards
        const appsWrapper = document.createElement('div');
        appsWrapper.className = 'apps-wrapper';
        
        // Si hay más de 3 apps, envolver en contenedor con scroll
        if (apps.length > 3) {
            const scrollContainer = document.createElement('div');
            scrollContainer.className = 'apps-scroll-container';
            scrollContainer.appendChild(appsWrapper);
            container.appendChild(scrollContainer);
        } else {
            container.appendChild(appsWrapper);
        }
        
        apps.forEach(app => {
            const sizeMB = (app.size / (1024 * 1024)).toFixed(1);
            const card = document.createElement('div');
            card.className = 'app-card';
            card.innerHTML = `
                <div class="app-card-content">
                    <div class="app-icon">
                        <img src="${app.iconURL}" alt="${app.name}" onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <span class="app-icon-fallback" style="display: none;">${getAppEmoji(app.name)}</span>
                    </div>
                    <div class="app-info">
                        <div class="app-name">${app.name}</div>
                        <div class="app-developer">${app.developerName}</div>
                        <div class="app-description">${app.localizedDescription || app.subtitle}</div>
                        <div class="app-meta">
                            <span class="app-version">${app.version}</span>
                            <span class="app-size">${sizeMB} MB</span>
                        </div>
                    </div>
                </div>
            `;
            appsWrapper.appendChild(card);
        });
    } else {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); grid-column: 1/-1;">No hay aplicaciones disponibles aún.</p>';
    }
}

// Load news from altstore.json
function loadNews(news) {
    const container = document.getElementById('news-container');
    
    if (news && news.length > 0) {
        news.forEach(item => {
            const date = new Date(item.date).toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            const card = document.createElement('div');
            card.className = 'news-card';
            card.innerHTML = `
                ${item.imageURL ? `<img class="news-image" src="${item.imageURL}" alt="${item.title}" onerror="this.style.display='none';">` : ''}
                <h3 class="news-title">${item.title}</h3>
                <p class="news-date">${date}</p>
                ${item.caption ? `<p class="news-description">${item.caption}</p>` : ''}
                ${item.url ? `<a href="${item.url}" target="_blank" class="news-link">Leer más →</a>` : ''}
            `;
            container.appendChild(card);
        });
    } else {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); grid-column: 1/-1;">No hay noticias aún.</p>';
    }
}

function getAppEmoji(name) {
    const emojis = {
        'Flycast': '🎮',
        'DolphiniOS': '🐬',
        'default': '📱'
    };
    return emojis[name] || emojis['default'];
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadAltStoreData();
    
    // Smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
