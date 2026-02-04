// Polpi MX - Enhanced Main Application JavaScript

const API_BASE = '';
// map declared in mapbox-map.js
var markers;
var currentListings = [];
var allListings = [];
var savedProperties = JSON.parse(localStorage.getItem('savedProperties') || '[]');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    updatePageTitle('Cargando CDMX...');
    showHeroIfFirstTime();
    
    // Initialize professional map with error handling
    try {
        initProfessionalMap();
    } catch (error) {
        console.error('Map initialization failed:', error);
    }
    
    loadStats();
    loadColonias();
    loadListings();
    setupEventListeners();
    setupKeyboardShortcuts();
});

// Show hero section for first-time visitors
function showHeroIfFirstTime() {
    const hasVisited = localStorage.getItem('hasVisited');
    if (!hasVisited) {
        document.getElementById('heroSection').style.display = 'block';
        initHeroChart();
        localStorage.setItem('hasVisited', 'true');
    } else {
        showDashboard();
    }
}

// Initialize hero chart
function initHeroChart() {
    const ctx = document.getElementById('heroChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            datasets: [{
                label: 'Propiedades CDMX agregadas',
                data: [35, 48, 67, 89, 112, 147],
                borderColor: '#8B5CF6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { 
                    beginAtZero: true,
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                x: { 
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
}

// Show dashboard
function showDashboard() {
    document.getElementById('dashboardSection').style.display = 'block';
    animateCounters();
}

// Animate dashboard counters
function animateCounters() {
    const counters = [
        { id: 'dashTotalProperties', target: 347 },
        { id: 'dashTotalColonias', target: 15 },
        { id: 'dashAvgPrice', target: 45000, prefix: '$', suffix: '/m²' },
        { id: 'dashBestDeal', target: 92 }
    ];

    counters.forEach(counter => {
        animateCounter(counter.id, 0, counter.target, counter.prefix, counter.suffix);
    });
}

// Animate individual counter
function animateCounter(elementId, start, end, prefix = '', suffix = '') {
    const element = document.getElementById(elementId);
    const duration = 2000;
    const increment = (end - start) / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        
        const value = Math.floor(current);
        const formatted = value.toLocaleString('es-MX');
        element.textContent = `${prefix}${formatted}${suffix}`;
    }, 16);
}

// Professional map is now initialized in mapbox-map.js
// This function is kept for compatibility
function initMap() {
    console.log('Map initialization delegated to professional map implementation');
}

// Load database statistics
async function loadStats() {
    try {
        const response = await fetchWithFallback('/api/v1/stats', '/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalListings').textContent = stats.total_listings || 0;
        document.getElementById('totalColonias').textContent = stats.colonias || 0;
        
        // Update hero stats if visible
        const heroProps = document.getElementById('heroTotalProperties');
        const heroColonias = document.getElementById('heroTotalColonias');
        if (heroProps) heroProps.textContent = `${stats.total_listings || 300}+`;
        if (heroColonias) heroColonias.textContent = stats.colonias || 15;
        
        // Update dashboard
        if (stats.total_listings) {
            document.getElementById('dashTotalProperties').textContent = stats.total_listings;
        }
        if (stats.colonias) {
            document.getElementById('dashTotalColonias').textContent = stats.colonias;
        }
        if (stats.avg_price_per_m2) {
            document.getElementById('dashAvgPrice').textContent = `$${Math.round(stats.avg_price_per_m2).toLocaleString('es-MX')}/m²`;
        }
        if (stats.best_deal_score) {
            document.getElementById('dashBestDeal').textContent = Math.round(stats.best_deal_score);
        }
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Fetch with fallback to v1 API then legacy API
async function fetchWithFallback(v1Url, fallbackUrl) {
    try {
        const response = await fetch(`${API_BASE}${v1Url}`);
        if (response.ok) return response;
        if (response.status === 404) {
            return await fetch(`${API_BASE}${fallbackUrl}`);
        }
        return response;
    } catch (error) {
        return await fetch(`${API_BASE}${fallbackUrl}`);
    }
}

// Load colonias for filters and neighborhood comparison
async function loadColonias() {
    try {
        const response = await fetchWithFallback('/api/v1/colonias', '/api/colonias');
        const colonias = await response.json();
        
        // Populate filter dropdown
        const coloniaFilter = document.getElementById('coloniaFilter');
        if (coloniaFilter) {
            colonias.forEach(colonia => {
                const option = document.createElement('option');
                option.value = colonia.colonia;
                option.textContent = `${colonia.colonia} (${colonia.count})`;
                coloniaFilter.appendChild(option);
            });
        }
        
        // Populate comparison dropdowns
        ['colonia1', 'colonia2', 'colonia3'].forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                colonias.forEach(colonia => {
                    const option = document.createElement('option');
                    option.value = colonia.colonia;
                    option.textContent = `${colonia.colonia} (${colonia.count})`;
                    select.appendChild(option);
                });
            }
        });
    } catch (error) {
        console.error('Error loading colonias:', error);
    }
}

// Load listings
async function loadListings(filters = {}) {
    try {
        showSkeletonLoaders();
        updatePageTitle('Cargando propiedades...');
        
        const params = new URLSearchParams(filters);
        const response = await fetchWithFallback(`/api/v1/listings?${params}`, `/api/listings?${params}`);
        const listings = await response.json();
        
        allListings = listings;
        currentListings = listings;
        
        hideLoadingStates();
        updateProfessionalMap(listings);
        renderListings(listings);
        updateResultsCount(listings.length);
        updatePageTitle(`${listings.length} propiedades en CDMX - Polpi MX`);
        
    } catch (error) {
        console.error('Error loading listings:', error);
        hideLoadingStates();
        showError('Error cargando propiedades');
        updatePageTitle('Error - Polpi MX CDMX');
    }
}

// Show skeleton loaders
function showSkeletonLoaders() {
    const grid = document.getElementById('listingsGrid');
    grid.innerHTML = Array(6).fill().map(() => `
        <div class="skeleton-card">
            <div class="skeleton skeleton-image"></div>
            <div class="skeleton skeleton-text"></div>
            <div class="skeleton skeleton-text short"></div>
            <div class="skeleton skeleton-text medium"></div>
        </div>
    `).join('');
    
    // Hide main loading spinner
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'none';
}

// Hide loading states
function hideLoadingStates() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'none';
}

// Legacy map function - replaced by professional implementation
// updateMap function is now handled by updateProfessionalMap in mapbox-map.js

// Legacy popup function - replaced by professional implementation
// Map popup content is now handled in mapbox-map.js

// Calculate deal score
function calculateDealScore(listing) {
    if (!listing.price_per_m2) return 0;
    
    // Simple scoring based on price per m2 relative to market averages
    const pricePerM2 = listing.price_per_m2;
    
    if (pricePerM2 < 25000) return Math.min(95, 80 + Math.random() * 15);
    if (pricePerM2 < 35000) return Math.min(85, 70 + Math.random() * 15);
    if (pricePerM2 < 50000) return Math.min(70, 55 + Math.random() * 15);
    if (pricePerM2 < 75000) return Math.min(55, 40 + Math.random() * 15);
    return Math.max(15, Math.random() * 25);
}

// Get deal score color
function getDealScoreColor(score) {
    if (score >= 75) return '#10B981'; // Green
    if (score >= 60) return '#84CC16'; // Lime
    if (score >= 40) return '#F59E0B'; // Orange
    return '#EF4444'; // Red
}

// Get deal score label
function getDealScoreLabel(score) {
    if (score >= 75) return 'Oportunidad';
    if (score >= 60) return 'Buen precio';
    if (score >= 40) return 'Precio justo';
    return 'Sobrepreciado';
}

// Render listings in grid
function renderListings(listings) {
    const grid = document.getElementById('listingsGrid');
    
    if (listings.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-content">
                    <i class="fas fa-home-alt"></i>
                    <h3>No se encontraron propiedades</h3>
                    <p>Intenta ajustar tus filtros de búsqueda</p>
                    <button id="clearFiltersEmpty" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Limpiar Filtros
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('clearFiltersEmpty')?.addEventListener('click', () => {
            clearAllFilters();
            loadListings();
        });
        return;
    }
    
    grid.innerHTML = listings.map(listing => createListingCard(listing)).join('');
    
    // Add event listeners
    setupCardEventListeners();
}

// Create enhanced listing card HTML
function createListingCard(listing) {
    const price = formatPrice(listing.price_mxn);
    const priceUSD = listing.price_usd ? `USD $${formatNumber(listing.price_usd)}` : '';
    const pricePerM2 = listing.price_per_m2 ? `${formatPrice(listing.price_per_m2)}/m²` : '';
    
    // Generate image - use picsum with listing ID as seed
    const image = `https://picsum.photos/seed/${listing.id}/800/600`;
    
    const dealScore = calculateDealScore(listing);
    const dealScoreClass = getDealScoreClass(dealScore);
    const dealScoreLabel = getDealScoreLabel(dealScore);
    
    // Check if property is new (last 7 days)
    const isNew = listing.scraped_date && 
        new Date() - new Date(listing.scraped_date) < 7 * 24 * 60 * 60 * 1000;
    
    const isFavorited = savedProperties.includes(listing.id);
    const isOpportunity = dealScore > 75;
    
    return `
        <div class="listing-card" data-id="${listing.id}" tabindex="0">
            <div class="listing-image-container">
                <img src="${image}" alt="${listing.title || 'Propiedad'}" class="listing-image" 
                     onerror="this.src='data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect fill="#1e1e2e" width="400" height="300"/><text fill="#8B5CF6" font-family="sans-serif" font-size="14" x="50%" y="45%" text-anchor="middle">${listing.property_type || 'Propiedad'}</text><text fill="#666" font-family="sans-serif" font-size="12" x="50%" y="55%" text-anchor="middle">${listing.city || ''}</text></svg>`)}'">
                
                <div class="listing-badges-overlay">
                    <div class="listing-badges-left">
                        ${dealScore ? `<div class="deal-score-badge ${dealScoreClass}">${Math.round(dealScore)}</div>` : ''}
                        ${isNew ? '<div class="status-badge nuevo">Nuevo</div>' : ''}
                        ${isOpportunity ? '<div class="status-badge oportunidad">Oportunidad</div>' : ''}
                    </div>
                    <div class="listing-badges-right">
                        <button class="favorite-btn ${isFavorited ? 'favorited' : ''}" onclick="toggleFavorite('${listing.id}', event)">
                            <i class="fa${isFavorited ? 's' : 'r'} fa-heart"></i>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="listing-content">
                <div class="listing-price">
                    ${price}
                    ${priceUSD ? `<div class="listing-price-usd">${priceUSD}</div>` : ''}
                </div>
                <div class="listing-title">${listing.title || `${listing.property_type} en ${listing.colonia}`}</div>
                <div class="listing-location">📍 ${listing.colonia || ''}, CDMX</div>
                <div class="listing-features">
                    ${listing.bedrooms ? `<div class="feature">🛏️ ${listing.bedrooms}</div>` : ''}
                    ${listing.bathrooms ? `<div class="feature">🚿 ${listing.bathrooms}</div>` : ''}
                    ${listing.size_m2 ? `<div class="feature">📐 ${listing.size_m2}m²</div>` : ''}
                    ${listing.parking_spaces ? `<div class="feature">🚗 ${listing.parking_spaces}</div>` : ''}
                </div>
                <div class="listing-footer">
                    <div class="listing-badges">
                        <div class="badge property-type ${listing.property_type?.toLowerCase()}">${listing.property_type}</div>
                        <div class="badge source">${listing.source}</div>
                    </div>
                    ${pricePerM2 ? `<span class="price-per-m2">${pricePerM2}</span>` : ''}
                </div>
            </div>
            
            <div class="quick-view-tooltip">
                <div class="tooltip-content">
                    <div class="tooltip-metric">
                        <span>Deal Score:</span>
                        <span>${Math.round(dealScore)} - ${dealScoreLabel}</span>
                    </div>
                    <div class="tooltip-metric">
                        <span>Precio/m²:</span>
                        <span>${pricePerM2}</span>
                    </div>
                    ${listing.lot_size_m2 ? `<div class="tooltip-metric"><span>Terreno:</span><span>${listing.lot_size_m2}m²</span></div>` : ''}
                    <div class="tooltip-metric">
                        <span>Fuente:</span>
                        <span>${listing.source}</span>
                    </div>
                </div>
                <div class="tooltip-arrow"></div>
            </div>
        </div>
    `;
}

// Get deal score CSS class
function getDealScoreClass(score) {
    if (score >= 75) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'poor';
}

// Setup card event listeners
function setupCardEventListeners() {
    document.querySelectorAll('.listing-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.favorite-btn')) {
                showListingDetail(card.dataset.id);
            }
        });
        
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                showListingDetail(card.dataset.id);
            }
        });
    });
}

// Toggle favorite
function toggleFavorite(listingId, event) {
    event.preventDefault();
    event.stopPropagation();
    
    const index = savedProperties.indexOf(listingId);
    const btn = event.currentTarget;
    const icon = btn.querySelector('i');
    
    if (index === -1) {
        savedProperties.push(listingId);
        btn.classList.add('favorited');
        icon.className = 'fas fa-heart';
        showToast('Propiedad guardada en favoritos');
    } else {
        savedProperties.splice(index, 1);
        btn.classList.remove('favorited');
        icon.className = 'far fa-heart';
        showToast('Propiedad removida de favoritos');
    }
    
    localStorage.setItem('savedProperties', JSON.stringify(savedProperties));
}

// Show toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    const messageEl = document.getElementById('toastMessage');
    
    messageEl.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Update results count
function updateResultsCount(count) {
    document.getElementById('listingCount').textContent = `${count} propiedades`;
}

// Update page title
function updatePageTitle(title) {
    document.title = title;
}

// Show listing detail modal (enhanced)
async function showListingDetail(listingId) {
    try {
        const response = await fetchWithFallback(`/api/v1/listing/${listingId}`, `/api/listing/${listingId}`);
        const listing = await response.json();
        
        // Load analysis data
        let analysis = {};
        try {
            const analysisResponse = await fetchWithFallback(`/api/v1/analyze/${listingId}`, `/api/analyze/${listingId}`);
            analysis = await analysisResponse.json();
        } catch (error) {
            console.error('Analysis not available:', error);
        }
        
        renderListingDetail(listing, analysis);
        document.getElementById('listingModal').classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Set up investment calculator
        setupInvestmentCalculator(listing);
        
    } catch (error) {
        console.error('Error loading listing detail:', error);
        showToast('Error al cargar los detalles de la propiedad');
    }
}

// Clear all filters
function clearAllFilters() {
    document.querySelectorAll('.filter-input').forEach(input => {
        input.value = '';
    });
    
    document.querySelectorAll('.property-type-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Activate "all" button
    document.querySelector('.property-type-btn[data-type=""]')?.classList.add('active');
    
    // Reset colonia filter specifically
    const coloniaFilter = document.getElementById('coloniaFilter');
    if (coloniaFilter) coloniaFilter.value = '';
}

// More functions will continue in the next part...
// Setup event listeners
function setupEventListeners() {
    // Hero section
    document.getElementById('dismissHero')?.addEventListener('click', () => {
        document.getElementById('heroSection').style.display = 'none';
        showDashboard();
    });
    
    document.getElementById('exploreBtn')?.addEventListener('click', () => {
        document.getElementById('heroSection').style.display = 'none';
        showDashboard();
        document.querySelector('.view-btn[data-view="list"]')?.click();
    });
    
    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const view = btn.dataset.view;
            document.getElementById(`${view}View`).classList.add('active');
            
            if (view === 'map' && map) {
                // Trigger map resize for Mapbox GL JS or Leaflet
                setTimeout(() => {
                    if (map.resize) {
                        map.resize(); // Mapbox GL JS
                    } else if (map.invalidateSize) {
                        map.invalidateSize(); // Leaflet fallback
                    }
                    
                    // Mark map as loaded for CSS styling
                    document.getElementById('map').classList.add('loaded');
                }, 100);
            }
            
            updatePageTitle(`Vista ${view === 'map' ? 'de mapa' : 'de lista'} CDMX - Polpi MX`);
        });
    });
    
    // Apply filters
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    
    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', () => {
        clearAllFilters();
        loadListings();
    });
    
    // Property type buttons
    document.querySelectorAll('.property-type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.property-type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
    
    // Best deals button
    document.getElementById('bestDealsBtn')?.addEventListener('click', () => {
        const bestDeals = currentListings
            .filter(listing => calculateDealScore(listing) > 75)
            .sort((a, b) => calculateDealScore(b) - calculateDealScore(a));
        renderListings(bestDeals);
        updateResultsCount(bestDeals.length);
        showToast(`${bestDeals.length} mejores ofertas encontradas`);
    });
    
    // Compare neighborhoods button
    document.getElementById('compareNeighborhoodsBtn')?.addEventListener('click', () => {
        document.getElementById('neighborhoodModal').classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    // Sort listings
    document.getElementById('sortBy').addEventListener('change', (e) => {
        sortListings(e.target.value);
    });
    
    // Modal close handlers
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // Modal tab handlers
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
    
    // Share button
    document.getElementById('shareListingBtn')?.addEventListener('click', () => {
        navigator.clipboard.writeText(window.location.href);
        showToast('Enlace copiado al portapapeles');
    });
    
    // Favorite button in modal
    document.getElementById('favoriteListingBtn')?.addEventListener('click', (e) => {
        const listingId = e.target.dataset.listingId;
        if (listingId) {
            toggleFavorite(listingId, e);
        }
    });
    
    // Toast close
    document.getElementById('toastClose')?.addEventListener('click', () => {
        document.getElementById('toast').classList.remove('show');
    });
    
    // Mobile filter toggle
    document.getElementById('mobileFilterBtn')?.addEventListener('click', () => {
        document.getElementById('filtersSidebar').classList.add('mobile-open');
        document.getElementById('mobileFilterOverlay').classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    document.getElementById('closeMobileFilters')?.addEventListener('click', closeMobileFilters);
    document.getElementById('mobileFilterOverlay')?.addEventListener('click', closeMobileFilters);
    
    // Global search
    document.getElementById('globalSearch')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performGlobalSearch();
        }
    });
    
    document.getElementById('searchBtn')?.addEventListener('click', performGlobalSearch);
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Escape key - close modals
        if (e.key === 'Escape') {
            closeModal();
            closeMobileFilters();
        }
        
        // Ctrl/Cmd + K - focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('globalSearch')?.focus();
        }
        
        // Arrow keys for navigating listings (when not in input)
        if (!e.target.matches('input, textarea, select')) {
            if (e.key === 'ArrowRight') {
                navigateListings(1);
            } else if (e.key === 'ArrowLeft') {
                navigateListings(-1);
            }
        }
    });
}

// Navigate listings with arrow keys
function navigateListings(direction) {
    const cards = document.querySelectorAll('.listing-card');
    const focused = document.activeElement;
    
    if (focused && focused.classList.contains('listing-card')) {
        const currentIndex = Array.from(cards).indexOf(focused);
        const nextIndex = currentIndex + direction;
        
        if (nextIndex >= 0 && nextIndex < cards.length) {
            cards[nextIndex].focus();
        }
    } else if (cards.length > 0) {
        cards[0].focus();
    }
}

// Close modal
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = '';
    updatePageTitle(document.querySelector('.view-btn.active')?.dataset.view === 'map' ? 'Vista de mapa CDMX - Polpi MX' : 'Vista de lista CDMX - Polpi MX');
}

// Close mobile filters
function closeMobileFilters() {
    document.getElementById('filtersSidebar').classList.remove('mobile-open');
    document.getElementById('mobileFilterOverlay').classList.remove('active');
    document.body.style.overflow = '';
}

// Switch tabs in modal
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

// Apply filters
function applyFilters() {
    const filters = {};
    
    const colonia = document.getElementById('coloniaFilter').value;
    if (colonia) filters.colonia = colonia;
    
    // Get active property type
    const activeTypeBtn = document.querySelector('.property-type-btn.active');
    const propertyType = activeTypeBtn?.dataset.type;
    if (propertyType) filters.property_type = propertyType;
    
    const minPrice = document.getElementById('minPrice').value;
    if (minPrice) filters.min_price = minPrice;
    
    const maxPrice = document.getElementById('maxPrice').value;
    if (maxPrice) filters.max_price = maxPrice;
    
    const bedrooms = document.getElementById('bedroomsFilter').value;
    if (bedrooms) filters.bedrooms = bedrooms;
    
    const bathrooms = document.getElementById('bathroomsFilter').value;
    if (bathrooms) filters.bathrooms = bathrooms;
    
    const minSize = document.getElementById('minSize').value;
    if (minSize) filters.min_size = minSize;
    
    const maxSize = document.getElementById('maxSize').value;
    if (maxSize) filters.max_size = maxSize;
    
    loadListings(filters);
    closeMobileFilters();
}

// Perform global search
function performGlobalSearch() {
    const query = document.getElementById('globalSearch').value;
    if (query.trim()) {
        const filters = { search: query };
        loadListings(filters);
        updatePageTitle(`Búsqueda en CDMX: ${query} - Polpi MX`);
    }
}

// Sort listings
function sortListings(sortBy) {
    let sorted = [...currentListings];
    
    switch (sortBy) {
        case 'price-low':
            sorted.sort((a, b) => (a.price_mxn || 0) - (b.price_mxn || 0));
            break;
        case 'price-high':
            sorted.sort((a, b) => (b.price_mxn || 0) - (a.price_mxn || 0));
            break;
        case 'deal-score':
            sorted.sort((a, b) => calculateDealScore(b) - calculateDealScore(a));
            break;
        case 'price-per-m2':
            sorted.sort((a, b) => (a.price_per_m2 || 0) - (b.price_per_m2 || 0));
            break;
        default: // recent
            // Already sorted by scraped_date DESC from API
            break;
    }
    
    currentListings = sorted;
    renderListings(sorted);
}

// Render listing detail (will be enhanced)
function renderListingDetail(listing, analysis) {
    const detailContainer = document.getElementById('listingDetail');
    const dealScore = analysis.deal_score || calculateDealScore(listing);
    
    const price = formatPrice(listing.price_mxn);
    const priceUSD = listing.price_usd ? `USD $${formatNumber(listing.price_usd)}` : '';
    const pricePerM2 = listing.price_per_m2 ? formatPrice(listing.price_per_m2) : 'N/A';
    
    // Generate multiple images
    const images = Array.from({length: 5}, (_, i) => 
        `https://picsum.photos/seed/${listing.id}-${i}/800/600`
    );
    
    let html = `
        <div class="detail-hero">
            <div class="detail-image-gallery">
                <img src="${images[0]}" alt="${listing.title || 'Propiedad'}" class="detail-image">
            </div>
            <div class="detail-overlay">
                <div class="detail-price">
                    ${price}
                    ${priceUSD ? `<div style="font-size: 1.2rem; color: #e5e7eb; opacity: 0.8;">${priceUSD}</div>` : ''}
                </div>
                <div class="detail-title">${listing.title || `${listing.property_type} en ${listing.colonia}`}</div>
                <div class="detail-location">
                    <i class="fas fa-map-marker-alt"></i> ${listing.colonia}, CDMX
                </div>
            </div>
        </div>
        
        <div class="detail-features">
            ${listing.bedrooms ? `<div class="detail-feature"><div class="detail-feature-icon"><i class="fas fa-bed"></i></div><div class="detail-feature-value">${listing.bedrooms}</div><div class="detail-feature-label">Recámaras</div></div>` : ''}
            ${listing.bathrooms ? `<div class="detail-feature"><div class="detail-feature-icon"><i class="fas fa-shower"></i></div><div class="detail-feature-value">${listing.bathrooms}</div><div class="detail-feature-label">Baños</div></div>` : ''}
            ${listing.size_m2 ? `<div class="detail-feature"><div class="detail-feature-icon"><i class="fas fa-ruler"></i></div><div class="detail-feature-value">${listing.size_m2}m²</div><div class="detail-feature-label">Superficie</div></div>` : ''}
            ${listing.parking_spaces ? `<div class="detail-feature"><div class="detail-feature-icon"><i class="fas fa-car"></i></div><div class="detail-feature-value">${listing.parking_spaces}</div><div class="detail-feature-label">Estacionamientos</div></div>` : ''}
            <div class="detail-feature">
                <div class="detail-feature-icon"><i class="fas fa-dollar-sign"></i></div>
                <div class="detail-feature-value">${pricePerM2}/m²</div>
                <div class="detail-feature-label">Precio por m²</div>
            </div>
        </div>
        
        ${listing.description ? `
            <div class="description-section">
                <h3>Descripción</h3>
                <p>${listing.description}</p>
            </div>
        ` : ''}
        
        <div class="contact-section">
            <div class="contact-info">
                ${listing.agent_name ? `<div class="contact-item"><i class="fas fa-user"></i> <strong>Agente:</strong> ${listing.agent_name}</div>` : ''}
                ${listing.agent_phone ? `<div class="contact-item"><i class="fas fa-phone"></i> <strong>Teléfono:</strong> ${listing.agent_phone}</div>` : ''}
                <div class="contact-item"><i class="fas fa-external-link-alt"></i> <strong>Fuente:</strong> ${listing.source}</div>
                ${listing.url ? `<div class="contact-item"><a href="${listing.url}" target="_blank" class="source-link">Ver anuncio original <i class="fas fa-arrow-right"></i></a></div>` : ''}
            </div>
        </div>
    `;
    
    detailContainer.innerHTML = html;
    
    // Set up analysis tab
    setupAnalysisTab(listing, analysis);
    
    // Set up neighborhood tab
    setupNeighborhoodTab(listing);
    
    // Update favorite button
    const favoriteBtn = document.getElementById('favoriteListingBtn');
    const isFavorited = savedProperties.includes(listing.id);
    if (favoriteBtn) {
        favoriteBtn.dataset.listingId = listing.id;
        favoriteBtn.querySelector('i').className = isFavorited ? 'fas fa-heart' : 'far fa-heart';
        favoriteBtn.style.color = isFavorited ? '#FFD700' : '';
    }
    
    // Update contact button
    const contactBtn = document.getElementById('contactAgentBtn');
    if (contactBtn && listing.agent_phone) {
        contactBtn.onclick = () => {
            window.open(`tel:${listing.agent_phone}`, '_blank');
        };
    }
}

// Setup analysis tab
function setupAnalysisTab(listing, analysis) {
    const dealScore = analysis.deal_score || calculateDealScore(listing);
    
    // Create deal score gauge
    setTimeout(() => {
        const canvas = document.getElementById('dealScoreGauge');
        if (canvas) {
            createDealScoreGauge(canvas, dealScore);
        }
    }, 100);
    
    // Update score text
    document.getElementById('dealScoreValue').textContent = Math.round(dealScore);
    document.getElementById('dealScoreLabel').textContent = getDealScoreLabel(dealScore);
    
    // Setup price comparison
    setupPriceComparison(listing, analysis);
    
    // Setup comparables
    setupComparables(analysis.comparables || []);
}

// More utility functions...
function formatPrice(price) {
    if (!price) return 'N/A';
    return `$${formatNumber(price)} MXN`;
}

function formatNumber(num) {
    return Math.round(num).toLocaleString('es-MX');
}

function showError(message) {
    const grid = document.getElementById('listingsGrid');
    grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <div class="empty-content">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="loadListings()" class="btn btn-primary">
                    <i class="fas fa-retry"></i> Reintentar
                </button>
            </div>
        </div>
    `;
}

// Make functions available globally
window.showListingDetail = showListingDetail;
window.toggleFavorite = toggleFavorite;

// Map compatibility functions
window.calculateDealScore = calculateDealScore;
window.getDealScoreClass = getDealScoreClass;
window.getDealScoreLabel = getDealScoreLabel;
window.getDealScoreColor = getDealScoreColor;
window.formatPrice = formatPrice;
window.formatNumber = formatNumber;