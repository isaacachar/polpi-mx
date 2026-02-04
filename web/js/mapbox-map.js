// Polpi MX - Professional MapLibre GL JS Implementation

let map;
let currentMarkers = [];
let clusteredProperties = [];
let hoveredPropertyId = null;
let popup = null;

// Property type colors and icons
const PROPERTY_STYLES = {
    casa: {
        color: '#3B82F6',
        icon: '🏠',
        textColor: '#FFFFFF'
    },
    departamento: {
        color: '#10B981', 
        icon: '🏢',
        textColor: '#FFFFFF'
    },
    terreno: {
        color: '#F59E0B',
        icon: '🏞️',
        textColor: '#FFFFFF'
    },
    oficina: {
        color: '#8B5CF6',
        icon: '🏢',
        textColor: '#FFFFFF'
    },
    default: {
        color: '#6B7280',
        icon: '🏠',
        textColor: '#FFFFFF'
    }
};

// Initialize professional MapLibre map
function initProfessionalMap() {
    // Check if MapLibre is loaded
    if (typeof maplibregl === 'undefined') {
        console.error('MapLibre GL JS failed to load, falling back to alternative...');
        initFallbackMap();
        return;
    }

    try {
        map = new maplibregl.Map({
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', // Free dark theme
            center: [-99.1332, 19.4326], // CDMX center
            zoom: 10,
            pitch: 45, // Slight 3D tilt for premium look
            bearing: 0,
            antialias: true, // Smooth graphics
            fadeDuration: 300, // Smooth transitions
            attributionControl: false // Clean look
        });

        // Add controls with custom styling
        map.addControl(new maplibregl.NavigationControl({
            showCompass: false,
            visualizePitch: true
        }), 'top-right');

        map.addControl(new maplibregl.FullscreenControl(), 'top-right');

        // Custom attribution
        map.addControl(new maplibregl.AttributionControl({
            compact: true,
            customAttribution: 'Polpi MX'
        }), 'bottom-right');

        // Map loaded event
        map.on('load', () => {
            console.log('Professional map loaded successfully');
            setupMapInteractions();
            
            // Mark map as loaded for CSS styling
            document.getElementById('map').classList.add('loaded');
        });

        // Error handling
        map.on('error', (e) => {
            console.error('MapLibre error, falling back:', e);
            initFallbackMap();
        });

    } catch (error) {
        console.error('MapLibre GL JS initialization failed:', error);
        initFallbackMap();
    }
}

// Setup map interactions
function setupMapInteractions() {
    // Disable map rotation using right click + drag
    map.dragRotate.disable();
    
    // Disable map rotation using touch rotation gesture
    map.touchZoomRotate.disableRotation();

    // Add hover cursor for properties
    map.on('mouseenter', 'properties', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    map.on('mouseleave', 'properties', () => {
        map.getCanvas().style.cursor = '';
    });
}

// Update map with property listings (main function)
function updateProfessionalMap(listings) {
    if (!map || !map.isStyleLoaded()) {
        console.log('Map not ready, retrying...');
        setTimeout(() => updateProfessionalMap(listings), 500);
        return;
    }

    // Clear existing markers
    clearMapMarkers();

    if (!listings || listings.length === 0) {
        return;
    }

    // Process listings for clustering
    const processedListings = processListingsForMap(listings);
    
    // Add clustered markers
    addClusteredMarkers(processedListings);
    
    // Add individual property markers
    addPropertyMarkers(processedListings);

    // Fit map to show all properties with padding
    fitMapToProperties(processedListings);
}

// Process listings for map display
function processListingsForMap(listings) {
    return listings
        .filter(listing => listing.lat && listing.lng && listing.price_mxn)
        .map(listing => ({
            ...listing,
            coordinates: [listing.lng, listing.lat],
            priceFormatted: formatMapPrice(listing.price_mxn),
            pricePerM2Formatted: listing.price_per_m2 ? formatMapPrice(listing.price_per_m2) + '/m²' : '',
            propertyStyle: PROPERTY_STYLES[listing.property_type?.toLowerCase()] || PROPERTY_STYLES.default,
            dealScore: calculateDealScore(listing)
        }));
}

// Format price for map display
function formatMapPrice(price) {
    if (!price) return 'N/A';
    
    if (price >= 1000000) {
        return '$' + (price / 1000000).toFixed(1) + 'M';
    } else if (price >= 1000) {
        return '$' + Math.round(price / 1000) + 'k';
    }
    return '$' + Math.round(price / 1000) + 'k';
}

// Add property markers with custom styling
function addPropertyMarkers(listings) {
    listings.forEach((listing, index) => {
        const el = createCustomMarker(listing);
        
        // Add entrance animation with staggered delay
        el.style.opacity = '0';
        el.style.transform = 'scale(0) translateY(20px)';
        
        const marker = new maplibregl.Marker({
            element: el,
            anchor: 'bottom'
        })
        .setLngLat(listing.coordinates)
        .addTo(map);

        // Animate marker appearance
        setTimeout(() => {
            el.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
            el.style.opacity = '1';
            el.style.transform = 'scale(1) translateY(0)';
        }, index * 50); // Staggered animation

        // Add click event
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            showListingDetail(listing.id);
        });

        // Add hover events
        el.addEventListener('mouseenter', (e) => {
            showPropertyHoverPopup(listing, e.target);
        });

        el.addEventListener('mouseleave', () => {
            hidePropertyHoverPopup();
        });

        currentMarkers.push(marker);
    });
}

// Create custom property marker element
function createCustomMarker(listing) {
    const el = document.createElement('div');
    el.className = 'custom-marker';
    el.innerHTML = `
        <div class="marker-pin" style="background: ${listing.propertyStyle.color};">
            <div class="marker-icon">${listing.propertyStyle.icon}</div>
        </div>
        <div class="marker-price" style="background: ${listing.propertyStyle.color}; color: ${listing.propertyStyle.textColor};">
            ${listing.priceFormatted}
        </div>
        <div class="marker-shadow"></div>
    `;
    
    // Add deal score indicator
    if (listing.dealScore > 75) {
        el.classList.add('opportunity-marker');
    }

    return el;
}

// Show property hover popup
function showPropertyHoverPopup(listing, markerElement) {
    hidePropertyHoverPopup(); // Hide any existing popup
    
    const popupContent = `
        <div class="map-popup-content">
            <div class="popup-image">
                <img src="https://picsum.photos/seed/${listing.id}/300/200" alt="${listing.title || 'Propiedad'}" 
                     onerror="this.style.display='none'">
            </div>
            <div class="popup-details">
                <div class="popup-price">${listing.priceFormatted}</div>
                <div class="popup-title">${listing.title || `${listing.property_type} en ${listing.colonia}`}</div>
                <div class="popup-location">${listing.colonia}, CDMX</div>
                <div class="popup-features">
                    ${listing.bedrooms ? `🛏️ ${listing.bedrooms}` : ''} 
                    ${listing.bathrooms ? `🚿 ${listing.bathrooms}` : ''} 
                    ${listing.size_m2 ? `📐 ${listing.size_m2}m²` : ''}
                </div>
                ${listing.pricePerM2Formatted ? `<div class="popup-price-m2">${listing.pricePerM2Formatted}</div>` : ''}
                <div class="popup-deal-score">
                    <span class="deal-score-badge ${getDealScoreClass(listing.dealScore)}">
                        ${Math.round(listing.dealScore)} - ${getDealScoreLabel(listing.dealScore)}
                    </span>
                </div>
            </div>
        </div>
    `;

    popup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        anchor: 'top',
        offset: [0, -10],
        className: 'custom-map-popup'
    })
    .setLngLat(listing.coordinates)
    .setHTML(popupContent)
    .addTo(map);
}

// Hide property hover popup
function hidePropertyHoverPopup() {
    if (popup) {
        popup.remove();
        popup = null;
    }
}

// Add clustered markers for dense areas
function addClusteredMarkers(listings) {
    const clusters = createPropertyClusters(listings);
    
    clusters.forEach(cluster => {
        if (cluster.properties.length > 1) {
            const el = createClusterMarker(cluster);
            
            const marker = new maplibregl.Marker({
                element: el,
                anchor: 'center'
            })
            .setLngLat([cluster.lng, cluster.lat])
            .addTo(map);

            // Add click event to zoom to cluster
            el.addEventListener('click', () => {
                map.flyTo({
                    center: [cluster.lng, cluster.lat],
                    zoom: Math.min(map.getZoom() + 2, 16),
                    duration: 1000
                });
            });

            currentMarkers.push(marker);
        }
    });
}

// Create cluster marker element
function createClusterMarker(cluster) {
    const el = document.createElement('div');
    el.className = 'cluster-marker';
    el.innerHTML = `
        <div class="cluster-count">${cluster.properties.length}</div>
        <div class="cluster-price">Avg ${formatMapPrice(cluster.avgPrice)}</div>
    `;
    return el;
}

// Simple clustering algorithm
function createPropertyClusters(listings) {
    const clusters = [];
    const processed = new Set();
    const CLUSTER_RADIUS = 0.005; // ~500m in degrees

    listings.forEach((listing, index) => {
        if (processed.has(index)) return;

        const cluster = {
            lat: listing.lat,
            lng: listing.lng,
            properties: [listing],
            totalPrice: listing.price_mxn
        };

        // Find nearby properties
        listings.forEach((otherListing, otherIndex) => {
            if (index === otherIndex || processed.has(otherIndex)) return;

            const distance = getDistance(listing.lat, listing.lng, otherListing.lat, otherListing.lng);
            if (distance < CLUSTER_RADIUS) {
                cluster.properties.push(otherListing);
                cluster.totalPrice += otherListing.price_mxn;
                processed.add(otherIndex);
            }
        });

        cluster.avgPrice = cluster.totalPrice / cluster.properties.length;
        clusters.push(cluster);
        processed.add(index);
    });

    return clusters;
}

// Calculate distance between two points
function getDistance(lat1, lng1, lat2, lng2) {
    const dLat = lat2 - lat1;
    const dLng = lng2 - lng1;
    return Math.sqrt(dLat * dLat + dLng * dLng);
}

// Fit map to show all properties
function fitMapToProperties(listings) {
    if (!listings.length) return;

    const coordinates = listings.map(listing => listing.coordinates);
    
    const bounds = coordinates.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));

    map.fitBounds(bounds, {
        padding: {
            top: 50,
            bottom: 50,
            left: 300, // Account for sidebar
            right: 50
        },
        maxZoom: 15,
        duration: 1000
    });
}

// Clear all markers from map
function clearMapMarkers() {
    currentMarkers.forEach(marker => marker.remove());
    currentMarkers = [];
    hidePropertyHoverPopup();
}

// Smooth fly-to animation for filtering
function flyToLocation(lng, lat, zoom = 12) {
    if (!map) return;
    
    map.flyTo({
        center: [lng, lat],
        zoom: zoom,
        duration: 1500,
        curve: 1.2
    });
}

// Fallback to premium Leaflet implementation if Mapbox fails
function initFallbackMap() {
    console.log('Initializing fallback map with premium tiles...');
    
    // Remove Mapbox container and create Leaflet container
    const mapContainer = document.getElementById('map');
    mapContainer.innerHTML = '<div id="leaflet-map" style="width: 100%; height: 100%;"></div>';
    
    // Load Leaflet dynamically
    loadLeafletFallback();
}

// Load Leaflet as fallback
function loadLeafletFallback() {
    // Add Leaflet CSS and JS dynamically
    const leafletCSS = document.createElement('link');
    leafletCSS.rel = 'stylesheet';
    leafletCSS.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(leafletCSS);

    const leafletJS = document.createElement('script');
    leafletJS.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    leafletJS.onload = () => {
        initPremiumLeafletMap();
    };
    document.head.appendChild(leafletJS);
}

// Initialize premium Leaflet map with better tiles
function initPremiumLeafletMap() {
    map = L.map('leaflet-map').setView([19.4326, -99.1332], 10);
    
    // Use CartoDB dark tiles (reliable, free, no API key)
    L.tileLayer('https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    console.log('Leaflet fallback map initialized with CartoDB dark tiles');
}

// Export functions for global access
if (typeof window !== 'undefined') {
    window.initProfessionalMap = initProfessionalMap;
    window.updateProfessionalMap = updateProfessionalMap;
    window.flyToLocation = flyToLocation;
    window.clearMapMarkers = clearMapMarkers;
}