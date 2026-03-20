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
        // Función para crear una card de noticia
        function createNewsCard(item) {
            const date = new Date(item.date).toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
            const card = document.createElement('div');
            card.className = 'news-card';
            card.innerHTML = `
                ${item.imageURL ? `<img class="news-card-image" src="${item.imageURL}" alt="${item.title}" onerror="this.style.display='none';">` : ''}
                <div class="news-card-content">
                    ${item.tintColor ? `<span class="news-category" style="color: #${item.tintColor}">Nueva</span>` : '<span class="news-category">Noticia</span>'}
                    <h3 class="news-title">${item.title}</h3>
                    <p class="news-date">${date}</p>
                    ${item.caption ? `<p class="news-description">${item.caption}</p>` : ''}
                    ${item.url ? `<a href="${item.url}" target="_blank" class="news-link">Leer más →</a>` : ''}
                </div>
            `;
            return card;
        }
        
        // Si hay más de 3 noticias, usar carrusel
        if (news.length > 3) {
            const carousel = document.createElement('div');
            carousel.className = 'news-carousel';
            
            const carouselInner = document.createElement('div');
            carouselInner.className = 'news-carousel-inner';
            
            // Crear slides mostrando 3 noticias, moviéndose de 1 en 1
            // Cada slide muestra noticias[i], noticias[i+1], noticias[i+2]
            const totalSlides = news.length;
            const slides = [];
            
            for (let i = 0; i < totalSlides; i++) {
                const slide = document.createElement('div');
                slide.className = 'news-carousel-slide';
                
                // Mostrar 3 noticias (con wrap-around)
                for (let j = 0; j < 3; j++) {
                    const index = (i + j) % totalSlides;
                    slide.appendChild(createNewsCard(news[index]));
                }
                
                carouselInner.appendChild(slide);
                slides.push(slide);
            }
            
            carousel.appendChild(carouselInner);
            
            let currentSlide = 0;
            
            // Crear indicadores
            const indicators = document.createElement('div');
            indicators.className = 'news-carousel-indicators';
            
            for (let i = 0; i < totalSlides; i++) {
                const indicator = document.createElement('div');
                indicator.className = 'news-carousel-indicator' + (i === 0 ? ' active' : '');
                indicator.addEventListener('click', () => {
                    currentSlide = i;
                    updateCarousel();
                });
                indicators.appendChild(indicator);
            }
            
            carousel.appendChild(indicators);
            container.appendChild(carousel);
            
            // Función para actualizar el carrusel
            function updateCarousel() {
                carouselInner.style.transform = `translateX(-${currentSlide * 100}%)`;
                
                // Actualizar indicadores
                document.querySelectorAll('.news-carousel-indicator').forEach((ind, idx) => {
                    ind.classList.toggle('active', idx === currentSlide);
                });
            }
            
            // Auto-rotar cada 5 segundos
            setInterval(() => {
                currentSlide = (currentSlide + 1) % totalSlides;
                updateCarousel();
            }, 5000);
        } else {
            // Si hay 3 o menos noticias, mostrarlas centradas sin carrusel
            news.forEach(item => {
                container.appendChild(createNewsCard(item));
            });
        }
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
