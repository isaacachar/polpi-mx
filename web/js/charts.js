// Polpi MX - Charts and Visualizations

// Create deal score gauge chart
function createDealScoreGauge(canvas, score) {
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: [
                    getDealScoreColor(score),
                    '#374151'
                ],
                borderWidth: 0,
                cutout: '75%'
            }]
        },
        options: {
            responsive: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            rotation: 270,
            circumference: 180
        }
    });
}

// Setup price comparison chart
function setupPriceComparison(listing, analysis) {
    if (!listing.price_per_m2) return;
    
    const marketAvg = analysis.neighborhood_stats?.avg_price_per_m2 || 45000;
    const propertyPrice = listing.price_per_m2;
    const maxPrice = Math.max(marketAvg * 1.5, propertyPrice * 1.2);
    
    const fillPercentage = (propertyPrice / maxPrice) * 100;
    const marketPercentage = (marketAvg / maxPrice) * 100;
    
    const fillEl = document.getElementById('priceComparisonFill');
    const markerEl = document.getElementById('marketMarker');
    
    if (fillEl) {
        fillEl.style.width = `${fillPercentage}%`;
        fillEl.textContent = formatPrice(propertyPrice);
    }
    
    if (markerEl) {
        markerEl.style.left = `${marketPercentage}%`;
    }
}

// Setup comparables
function setupComparables(comparables) {
    const container = document.getElementById('comparablesList');
    if (!container) return;
    
    if (comparables.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #6b7280; margin: 2rem 0;">No se encontraron propiedades comparables</p>';
        return;
    }
    
    container.innerHTML = comparables.map(comp => `
        <div class="comparable-card">
            <div class="comparable-price">${formatPrice(comp.price_mxn)}</div>
            <div class="comparable-location">${comp.colonia}, CDMX</div>
            <div class="comparable-features">
                ${comp.bedrooms ? `🛏️ ${comp.bedrooms}` : ''}
                ${comp.bathrooms ? `🚿 ${comp.bathrooms}` : ''}
                ${comp.size_m2 ? `📐 ${comp.size_m2}m²` : ''}
            </div>
            ${comp.price_per_m2 ? `<div style="font-size: 0.8rem; color: #8B5CF6; margin-top: 0.5rem;">${formatPrice(comp.price_per_m2)}/m²</div>` : ''}
        </div>
    `).join('');
}

// Setup neighborhood tab
function setupNeighborhoodTab(listing) {
    loadNeighborhoodStats(listing.colonia, 'CDMX');
    loadNearbyListings(listing.lat, listing.lng, listing.id);
}

// Load neighborhood stats
async function loadNeighborhoodStats(colonia, city = 'CDMX') {
    try {
        const response = await fetchWithFallback(`/api/v1/neighborhood/stats?colonia=${encodeURIComponent(colonia)}&city=${encodeURIComponent(city)}`, `/api/neighborhood/stats?colonia=${encodeURIComponent(colonia)}&city=${encodeURIComponent(city)}`);
        const stats = await response.json();
        
        const container = document.getElementById('neighborhoodStatsContent');
        if (!container) return;
        
        container.innerHTML = `
            <div class="neighborhood-stats-grid">
                <div class="neighborhood-stat-card">
                    <div class="neighborhood-stat-value">${formatPrice(stats.avg_price_mxn || 0)}</div>
                    <div class="neighborhood-stat-label">Precio Promedio</div>
                </div>
                <div class="neighborhood-stat-card">
                    <div class="neighborhood-stat-value">${formatPrice(stats.avg_price_per_m2 || 0)}/m²</div>
                    <div class="neighborhood-stat-label">Precio por m²</div>
                </div>
                <div class="neighborhood-stat-card">
                    <div class="neighborhood-stat-value">${stats.listing_count || 0}</div>
                    <div class="neighborhood-stat-label">Propiedades</div>
                </div>
                <div class="neighborhood-stat-card">
                    <div class="neighborhood-stat-value">${stats.avg_size_m2 || 0}m²</div>
                    <div class="neighborhood-stat-label">Tamaño Promedio</div>
                </div>
            </div>
            
            ${stats.price_trend ? `
                <div class="price-trend-chart">
                    <h4>Tendencia de Precios (últimos 6 meses)</h4>
                    <canvas id="neighborhoodTrendChart" width="400" height="200"></canvas>
                </div>
            ` : ''}
        `;
        
        // Create trend chart if data available
        if (stats.price_trend && stats.price_trend.length > 1) {
            setTimeout(() => {
                createNeighborhoodTrendChart(stats.price_trend);
            }, 100);
        }
        
    } catch (error) {
        console.error('Error loading neighborhood stats:', error);
        const container = document.getElementById('neighborhoodStatsContent');
        if (container) {
            container.innerHTML = '<p style="text-align: center; color: #6b7280; margin: 2rem 0;">No se pudieron cargar las estadísticas del vecindario</p>';
        }
    }
}

// Create neighborhood trend chart
function createNeighborhoodTrendChart(trendData) {
    const canvas = document.getElementById('neighborhoodTrendChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trendData.map(d => d.month),
            datasets: [{
                label: 'Precio promedio/m²',
                data: trendData.map(d => d.avg_price_per_m2),
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
                    beginAtZero: false,
                    grid: { color: '#374151' },
                    ticks: { 
                        color: '#9CA3AF',
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'k';
                        }
                    }
                },
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                }
            }
        }
    });
}

// Load nearby listings
async function loadNearbyListings(lat, lng, excludeId) {
    if (!lat || !lng) return;
    
    try {
        const response = await fetchWithFallback(`/api/v1/nearby?lat=${lat}&lng=${lng}&radius=2&limit=6&exclude=${excludeId}`, `/api/nearby?lat=${lat}&lng=${lng}&radius=2&limit=6&exclude=${excludeId}`);
        const listings = await response.json();
        
        const container = document.getElementById('nearbyListings');
        if (!container) return;
        
        if (listings.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #6b7280; margin: 2rem 0;">No se encontraron propiedades cercanas</p>';
            return;
        }
        
        container.innerHTML = listings.map(listing => `
            <div class="nearby-listing-card" onclick="showListingDetail('${listing.id}')">
                <div class="nearby-listing-price">${formatPrice(listing.price_mxn)}</div>
                <div class="nearby-listing-details">
                    <div style="margin-bottom: 0.25rem;">${listing.colonia}</div>
                    <div style="font-size: 0.75rem; color: #6b7280;">
                        ${listing.bedrooms ? `🛏️ ${listing.bedrooms}` : ''} 
                        ${listing.bathrooms ? `🚿 ${listing.bathrooms}` : ''} 
                        ${listing.size_m2 ? `📐 ${listing.size_m2}m²` : ''}
                    </div>
                    ${listing.price_per_m2 ? `<div style="color: #8B5CF6; font-size: 0.75rem; margin-top: 0.25rem;">${formatPrice(listing.price_per_m2)}/m²</div>` : ''}
                    <div style="font-size: 0.7rem; color: #6b7280; margin-top: 0.25rem;">${calculateDistance(lat, lng, listing.lat, listing.lng).toFixed(1)} km</div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading nearby listings:', error);
        const container = document.getElementById('nearbyListings');
        if (container) {
            container.innerHTML = '<p style="text-align: center; color: #6b7280; margin: 2rem 0;">No se pudieron cargar las propiedades cercanas</p>';
        }
    }
}

// Calculate distance between two coordinates (Haversine formula)
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

// Create price trend chart for dashboard
function createPriceTrendChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = 600;
    canvas.height = 300;
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: data.datasets.map((dataset, index) => ({
                label: dataset.label,
                data: dataset.data,
                borderColor: index === 0 ? '#8B5CF6' : index === 1 ? '#10B981' : '#F59E0B',
                backgroundColor: index === 0 ? 'rgba(139, 92, 246, 0.1)' : index === 1 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                tension: 0.4,
                fill: false
            }))
        },
        options: {
            responsive: true,
            interaction: {
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#e5e7eb',
                        usePointStyle: true,
                        pointStyle: 'line'
                    }
                },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#f3f4f6',
                    bodyColor: '#e5e7eb',
                    borderColor: '#374151',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    beginAtZero: false,
                    grid: { color: '#374151' },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'k/m²';
                        }
                    }
                }
            }
        }
    });
}

// Load and display price trends for CDMX colonias
async function loadColoniaPriceTrends() {
    try {
        const response = await fetchWithFallback('/api/v1/trends/colonias', '/api/trends/colonias');
        const trends = await response.json();
        
        // Create chart data
        const chartData = {
            labels: trends.months || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            datasets: trends.colonias?.slice(0, 3).map(colonia => ({
                label: colonia.name,
                data: colonia.price_trend
            })) || []
        };
        
        if (chartData.datasets.length > 0) {
            createPriceTrendChart('coloniaTrendsChart', chartData);
        }
        
    } catch (error) {
        console.error('Error loading colonia price trends:', error);
    }
}

// Export functions for use in other files
if (typeof window !== 'undefined') {
    window.createDealScoreGauge = createDealScoreGauge;
    window.setupPriceComparison = setupPriceComparison;
    window.setupComparables = setupComparables;
    window.setupNeighborhoodTab = setupNeighborhoodTab;
    window.loadColoniaPriceTrends = loadColoniaPriceTrends;
}