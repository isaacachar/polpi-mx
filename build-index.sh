#!/bin/bash

# Build the complete self-contained index.html

cat > docs/index.html << 'ENDOFHEADER'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Polpi MX - Propiedades en CDMX</title>
    <meta name="description" content="Encuentra tu próximo hogar en Ciudad de México. Miles de propiedades en venta y renta.">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🐙</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-blue: #006AFF;
            --primary-hover: #0052CC;
            --bg-white: #ffffff;
            --bg-gray: #f7f7f7;
            --text-primary: #1a1a1a;
            --text-secondary: #555555;
            --text-muted: #888888;
            --border-color: #e0e0e0;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-gray);
            color: var(--text-primary);
            line-height: 1.5;
        }

        .navbar {
            background: var(--bg-white);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: var(--shadow-sm);
        }

        .nav-container {
            max-width: 1920px;
            margin: 0 auto;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 64px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            text-decoration: none;
        }

        .logo-emoji {
            font-size: 28px;
        }

        .search-bar {
            flex: 1;
            max-width: 600px;
            margin: 0 40px;
        }

        .search-input {
            width: 100%;
            padding: 12px 16px 12px 44px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            background: var(--bg-white);
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23888888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'%3E%3C/circle%3E%3Cpath d='m21 21-4.35-4.35'%3E%3C/path%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 14px center;
            transition: all 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(0, 106, 255, 0.1);
        }

        .nav-links {
            display: flex;
            gap: 24px;
            align-items: center;
        }

        .nav-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
            transition: color 0.2s;
        }

        .nav-link:hover {
            color: var(--primary-blue);
        }

        .filters {
            background: var(--bg-white);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
            position: sticky;
            top: 64px;
            z-index: 999;
        }

        .filters-container {
            max-width: 1920px;
            margin: 0 auto;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        .filter-pill {
            padding: 10px 18px;
            border: 1px solid var(--border-color);
            border-radius: 24px;
            background: var(--bg-white);
            color: var(--text-primary);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
            user-select: none;
        }

        .filter-pill:hover {
            border-color: var(--primary-blue);
            background: rgba(0, 106, 255, 0.05);
        }

        .filter-pill.active {
            background: var(--primary-blue);
            color: white;
            border-color: var(--primary-blue);
        }

        .results-count {
            margin-left: auto;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
        }

        .main-container {
            max-width: 1920px;
            margin: 0 auto;
            display: flex;
            height: calc(100vh - 144px);
        }

        .map-panel {
            flex: 0 0 45%;
            position: sticky;
            top: 144px;
            height: calc(100vh - 144px);
        }

        #map {
            width: 100%;
            height: 100%;
        }

        .listings-panel {
            flex: 1;
            overflow-y: auto;
            background: var(--bg-gray);
            padding: 24px;
        }

        .listing-card {
            background: var(--bg-white);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        .listing-card:hover {
            box-shadow: var(--shadow-lg);
            border-color: var(--border-color);
        }

        .listing-card.highlighted {
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(0, 106, 255, 0.1);
        }

        .listing-image {
            width: 100%;
            height: 220px;
            background: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }

        .listing-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .listing-image .placeholder-icon {
            font-size: 64px;
            opacity: 0.3;
        }

        .listing-content {
            padding: 16px;
        }

        .listing-price {
            font-size: 22px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .listing-details {
            display: flex;
            gap: 16px;
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 8px;
            align-items: center;
        }

        .listing-detail {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .listing-location {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 4px;
        }

        .listing-title {
            color: var(--text-muted);
            font-size: 13px;
        }

        .marker {
            background: var(--primary-blue);
            color: white;
            padding: 6px 10px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            box-shadow: var(--shadow-md);
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .marker:hover {
            background: var(--primary-hover);
            transform: scale(1.1);
        }

        .marker.highlighted {
            background: #e74c3c;
            transform: scale(1.15);
            z-index: 100;
        }

        .footer {
            background: var(--bg-white);
            border-top: 1px solid var(--border-color);
            padding: 32px 24px;
            text-align: center;
        }

        .footer-content {
            max-width: 1920px;
            margin: 0 auto;
            color: var(--text-secondary);
            font-size: 14px;
        }

        .footer-links {
            display: flex;
            gap: 24px;
            justify-center;
            margin-top: 16px;
        }

        .footer-link {
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
        }

        .footer-link:hover {
            color: var(--primary-blue);
        }

        @media (max-width: 1024px) {
            .main-container {
                flex-direction: column;
                height: auto;
            }

            .map-panel {
                flex: none;
                position: relative;
                height: 400px;
                top: 0;
            }

            .listings-panel {
                height: auto;
            }

            .search-bar {
                margin: 0 16px;
            }

            .nav-links {
                display: none;
            }
        }

        @media (max-width: 768px) {
            .nav-container {
                padding: 0 16px;
            }

            .search-bar {
                max-width: none;
                margin: 0 12px;
            }

            .filters-container {
                gap: 8px;
            }

            .filter-pill {
                padding: 8px 14px;
                font-size: 13px;
            }

            .listings-panel {
                padding: 16px;
            }

            .listing-price {
                font-size: 20px;
            }

            .map-panel {
                height: 300px;
            }
        }

        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 48px;
            color: var(--text-secondary);
        }

        .filter-dropdown {
            position: relative;
        }

        .dropdown-content {
            display: none;
            position: absolute;
            top: calc(100% + 8px);
            left: 0;
            background: var(--bg-white);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            padding: 12px;
            min-width: 200px;
            z-index: 1000;
        }

        .dropdown-content.active {
            display: block;
        }

        .dropdown-option {
            padding: 8px 12px;
            cursor: pointer;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .dropdown-option:hover {
            background: var(--bg-gray);
        }

        .dropdown-option.selected {
            background: rgba(0, 106, 255, 0.1);
            color: var(--primary-blue);
            font-weight: 500;
        }

        .price-range-inputs {
            display: flex;
            gap: 8px;
            padding: 8px 0;
        }

        .price-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 13px;
        }

        .apply-button {
            width: 100%;
            padding: 8px 16px;
            background: var(--primary-blue);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            margin-top: 8px;
            transition: background 0.2s;
        }

        .apply-button:hover {
            background: var(--primary-hover);
        }

        /* Skeleton Loaders */
        .skeleton-card {
            background: var(--bg-white);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 16px;
            animation: pulse 1.5s ease-in-out infinite;
        }

        .skeleton {
            background: linear-gradient(
                90deg,
                #f0f0f0 25%,
                #e0e0e0 50%,
                #f0f0f0 75%
            );
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }

        @keyframes shimmer {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }

        .skeleton-image {
            width: 100%;
            height: 220px;
        }

        .skeleton-content {
            padding: 16px;
        }

        .skeleton-text {
            height: 20px;
            border-radius: 4px;
            margin-bottom: 12px;
        }

        .skeleton-text.short {
            width: 60%;
        }

        .skeleton-text.title {
            height: 24px;
            width: 40%;
            margin-bottom: 16px;
        }

        .skeleton-details {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
        }

        .skeleton-detail {
            height: 16px;
            width: 60px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">
                <span class="logo-emoji">🐙</span>
                <span>Polpi MX</span>
            </a>
            <div class="search-bar">
                <input 
                    type="text" 
                    class="search-input" 
                    placeholder="Busca por colonia, dirección o código postal..."
                    id="searchInput"
                >
            </div>
            <div class="nav-links">
                <a href="#" class="nav-link">Comprar</a>
                <a href="#" class="nav-link">Rentar</a>
                <a href="#" class="nav-link">Nosotros</a>
            </div>
        </div>
    </nav>

    <div class="filters">
        <div class="filters-container">
            <div class="filter-pill active" data-filter="type" data-value="sale">
                En Venta
            </div>
            
            <div class="filter-dropdown">
                <div class="filter-pill" id="priceFilter">
                    Precio ▾
                </div>
                <div class="dropdown-content" id="priceDropdown">
                    <div class="price-range-inputs">
                        <input type="number" class="price-input" placeholder="Mín" id="minPrice">
                        <input type="number" class="price-input" placeholder="Máx" id="maxPrice">
                    </div>
                    <button class="apply-button" onclick="applyPriceFilter()">Aplicar</button>
                </div>
            </div>

            <div class="filter-dropdown">
                <div class="filter-pill" id="bedroomsFilter">
                    Recámaras ▾
                </div>
                <div class="dropdown-content" id="bedroomsDropdown">
                    <div class="dropdown-option" onclick="selectBedrooms('any')">Cualquiera</div>
                    <div class="dropdown-option" onclick="selectBedrooms(1)">1+</div>
                    <div class="dropdown-option" onclick="selectBedrooms(2)">2+</div>
                    <div class="dropdown-option" onclick="selectBedrooms(3)">3+</div>
                    <div class="dropdown-option" onclick="selectBedrooms(4)">4+</div>
                </div>
            </div>

            <div class="filter-dropdown">
                <div class="filter-pill" id="propertyTypeFilter">
                    Tipo ▾
                </div>
                <div class="dropdown-content" id="propertyTypeDropdown">
                    <div class="dropdown-option selected" onclick="selectPropertyType('all')">Todos</div>
                    <div class="dropdown-option" onclick="selectPropertyType('Departamento')">Departamento</div>
                    <div class="dropdown-option" onclick="selectPropertyType('Casa')">Casa</div>
                </div>
            </div>

            <span class="results-count" id="resultsCount">549 resultados en CDMX</span>
        </div>
    </div>

    <div class="main-container">
        <div class="map-panel">
            <div id="map"></div>
        </div>
        <div class="listings-panel" id="listingsPanel">
            <!-- Skeleton loaders -->
            <div class="skeleton-card">
                <div class="skeleton skeleton-image"></div>
                <div class="skeleton-content">
                    <div class="skeleton skeleton-text title"></div>
                    <div class="skeleton-details">
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                    </div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text short"></div>
                </div>
            </div>
            <div class="skeleton-card">
                <div class="skeleton skeleton-image"></div>
                <div class="skeleton-content">
                    <div class="skeleton skeleton-text title"></div>
                    <div class="skeleton-details">
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                    </div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text short"></div>
                </div>
            </div>
            <div class="skeleton-card">
                <div class="skeleton skeleton-image"></div>
                <div class="skeleton-content">
                    <div class="skeleton skeleton-text title"></div>
                    <div class="skeleton-details">
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                        <div class="skeleton skeleton-detail"></div>
                    </div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text short"></div>
                </div>
            </div>
        </div>
    </div>

    <footer class="footer">
        <div class="footer-content">
            <p>© 2026 Polpi MX · Inteligencia Inmobiliaria · CDMX</p>
            <div class="footer-links">
                <a href="#" class="footer-link">Términos</a>
                <a href="#" class="footer-link">Privacidad</a>
                <a href="#" class="footer-link">Contacto</a>
            </div>
        </div>
    </footer>

    <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
    <script>
        const LISTINGS_DATA = 
ENDOFHEADER

# Add the listings data
cat docs/js/data-listings.json >> docs/index.html

# Add the rest of the JavaScript
cat >> docs/index.html << 'ENDOFJS'
;

        // State
        let map;
        let markers = [];
        let filteredListings = [...LISTINGS_DATA];
        let filters = {
            search: '',
            minPrice: null,
            maxPrice: null,
            bedrooms: null,
            propertyType: 'all'
        };

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initMap();
            renderListings();
            setupEventListeners();
        });

        function initMap() {
            map = new maplibregl.Map({
                container: 'map',
                style: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
                center: [-99.1332, 19.4326],
                zoom: 11
            });

            map.addControl(new maplibregl.NavigationControl());
        }

        function formatPrice(price) {
            if (!price) return "Precio no disponible";
            return '$' + price.toLocaleString('es-MX') + ' MXN';
        }

        function formatPriceShort(price) {
            if (!price) return "N/A";
            if (price >= 1000000) {
                return '$' + (price / 1000000).toFixed(1) + 'M';
            }
            return '$' + (price / 1000).toFixed(0) + 'K';
        }

        function renderListings() {
            const panel = document.getElementById('listingsPanel');
            
            if (filteredListings.length === 0) {
                panel.innerHTML = '<div class="loading">No se encontraron resultados</div>';
                clearMarkers();
                return;
            }

            panel.innerHTML = filteredListings.map(listing => {
                // Parse images if stored as JSON string
                let images = [];
                if (listing.images) {
                    try {
                        images = typeof listing.images === 'string' 
                            ? JSON.parse(listing.images) 
                            : listing.images;
                    } catch (e) {
                        images = [];
                    }
                }
                
                return `
                    <div class="listing-card" data-id="${listing.id}" onclick="highlightListing('${listing.id}')">
                        <div class="listing-image">
                            ${images && images[0] 
                                ? `<img src="${images[0]}" alt="${listing.title}" onerror="this.parentElement.innerHTML='<span class=\\'placeholder-icon\\'>🏠</span>'">`
                                : '<span class="placeholder-icon">🏠</span>'
                            }
                        </div>
                        <div class="listing-content">
                            <div class="listing-price">${formatPrice(listing.price_mxn)}</div>
                            <div class="listing-details">
                                ${listing.bedrooms ? `<span class="listing-detail">${listing.bedrooms} rec</span>` : ''}
                                ${listing.bathrooms ? `<span class="listing-detail">· ${listing.bathrooms} baños</span>` : ''}
                                ${listing.size_m2 ? `<span class="listing-detail">· ${Math.round(listing.size_m2)} m²</span>` : ''}
                            </div>
                            <div class="listing-location">${listing.colonia || listing.city}</div>
                            <div class="listing-title">${listing.title}</div>
                        </div>
                    </div>
                `;
            }).join('');

            updateResultsCount();
            renderMarkers();
        }

        function renderMarkers() {
            clearMarkers();

            filteredListings.forEach(listing => {
                if (!listing.lat || !listing.lng) return;

                const el = document.createElement('div');
                el.className = 'marker';
                el.textContent = formatPriceShort(listing.price_mxn);
                el.dataset.id = listing.id;

                el.addEventListener('click', () => {
                    highlightListing(listing.id);
                    const card = document.querySelector(`[data-id="${listing.id}"]`);
                    if (card) {
                        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                });

                const marker = new maplibregl.Marker({ element: el })
                    .setLngLat([listing.lng, listing.lat])
                    .addTo(map);

                markers.push({ marker, id: listing.id, element: el });
            });
        }

        function clearMarkers() {
            markers.forEach(({ marker }) => marker.remove());
            markers = [];
        }

        function highlightListing(id) {
            document.querySelectorAll('.listing-card').forEach(card => {
                card.classList.remove('highlighted');
            });
            document.querySelectorAll('.marker').forEach(marker => {
                marker.classList.remove('highlighted');
            });

            const card = document.querySelector(`.listing-card[data-id="${id}"]`);
            if (card) card.classList.add('highlighted');

            const markerObj = markers.find(m => m.id === id);
            if (markerObj) markerObj.element.classList.add('highlighted');
        }

        function applyFilters() {
            filteredListings = LISTINGS_DATA.filter(listing => {
                if (filters.search) {
                    const search = filters.search.toLowerCase();
                    const searchableText = `${listing.title} ${listing.colonia} ${listing.description}`.toLowerCase();
                    if (!searchableText.includes(search)) return false;
                }

                if (filters.minPrice && listing.price_mxn < filters.minPrice) return false;
                if (filters.maxPrice && listing.price_mxn > filters.maxPrice) return false;
                
                if (filters.bedrooms && listing.bedrooms < filters.bedrooms) return false;
                
                if (filters.propertyType !== 'all') {
                    const titleLower = listing.title.toLowerCase();
                    if (filters.propertyType === 'Departamento' && !titleLower.includes('departamento')) return false;
                    if (filters.propertyType === 'Casa' && !titleLower.includes('casa')) return false;
                }

                return true;
            });

            renderListings();
        }

        function updateResultsCount() {
            const count = document.getElementById('resultsCount');
            count.textContent = `${filteredListings.length} resultado${filteredListings.length !== 1 ? 's' : ''} en CDMX`;
        }

        function setupEventListeners() {
            const searchInput = document.getElementById('searchInput');
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    filters.search = e.target.value;
                    applyFilters();
                }, 300);
            });

            document.getElementById('priceFilter').addEventListener('click', () => {
                toggleDropdown('priceDropdown');
            });

            document.getElementById('bedroomsFilter').addEventListener('click', () => {
                toggleDropdown('bedroomsDropdown');
            });

            document.getElementById('propertyTypeFilter').addEventListener('click', () => {
                toggleDropdown('propertyTypeDropdown');
            });

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.filter-dropdown')) {
                    document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('active'));
                }
            });
        }

        function toggleDropdown(id) {
            const dropdown = document.getElementById(id);
            const isActive = dropdown.classList.contains('active');
            
            document.querySelectorAll('.dropdown-content').forEach(d => d.classList.remove('active'));
            
            if (!isActive) {
                dropdown.classList.add('active');
            }
        }

        function applyPriceFilter() {
            const min = document.getElementById('minPrice').value;
            const max = document.getElementById('maxPrice').value;
            
            filters.minPrice = min ? parseInt(min) : null;
            filters.maxPrice = max ? parseInt(max) : null;
            
            applyFilters();
            toggleDropdown('priceDropdown');
        }

        function selectBedrooms(value) {
            filters.bedrooms = value === 'any' ? null : parseInt(value);
            applyFilters();
            toggleDropdown('bedroomsDropdown');

            document.querySelectorAll('#bedroomsDropdown .dropdown-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            event.target.classList.add('selected');
        }

        function selectPropertyType(value) {
            filters.propertyType = value;
            applyFilters();
            toggleDropdown('propertyTypeDropdown');

            document.querySelectorAll('#propertyTypeDropdown .dropdown-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            event.target.classList.add('selected');
        }
    </script>
</body>
</html>
ENDOFJS

echo "Build complete!"
