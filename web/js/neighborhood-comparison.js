// Polpi MX - Neighborhood Comparison Tool

// Setup neighborhood comparison modal
document.addEventListener('DOMContentLoaded', () => {
    setupNeighborhoodComparison();
});

function setupNeighborhoodComparison() {
    const compareBtn = document.getElementById('compareBtn');
    const modalClose = document.getElementById('neighborhoodModalClose');
    
    if (compareBtn) {
        compareBtn.addEventListener('click', performNeighborhoodComparison);
    }
    
    if (modalClose) {
        modalClose.addEventListener('click', closeNeighborhoodModal);
    }
}

// Perform neighborhood comparison
async function performNeighborhoodComparison() {
    const colonia1 = document.getElementById('colonia1')?.value;
    const colonia2 = document.getElementById('colonia2')?.value;
    const colonia3 = document.getElementById('colonia3')?.value;
    
    if (!colonia1 || !colonia2) {
        showToast('Por favor selecciona al menos 2 colonias para comparar');
        return;
    }
    
    const colonias = [colonia1, colonia2];
    if (colonia3) colonias.push(colonia3);
    
    try {
        showComparisonLoading();
        
        const response = await fetchWithFallback(
            `/api/v1/neighborhoods/compare?colonias=${encodeURIComponent(colonias.join(','))}`,
            `/api/neighborhoods/compare?colonias=${encodeURIComponent(colonias.join(','))}`
        );
        
        const comparisonData = await response.json();
        displayComparisonResults(comparisonData);
        
    } catch (error) {
        console.error('Error performing neighborhood comparison:', error);
        showComparisonError();
    }
}

// Show loading state for comparison
function showComparisonLoading() {
    const resultsContainer = document.getElementById('comparisonResults');
    if (!resultsContainer) return;
    
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="comparison-loading">
            <div class="spinner"></div>
            <p>Comparando colonias...</p>
        </div>
    `;
}

// Show comparison error
function showComparisonError() {
    const resultsContainer = document.getElementById('comparisonResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="comparison-error">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error al comparar colonias</h3>
            <p>No se pudieron cargar los datos de comparación. Intenta de nuevo.</p>
            <button onclick="performNeighborhoodComparison()" class="btn btn-primary">
                <i class="fas fa-retry"></i> Reintentar
            </button>
        </div>
    `;
}

// Display comparison results
function displayComparisonResults(data) {
    const resultsContainer = document.getElementById('comparisonResults');
    if (!resultsContainer) return;
    
    if (!data.neighborhoods || data.neighborhoods.length === 0) {
        resultsContainer.innerHTML = `
            <div class="comparison-error">
                <i class="fas fa-info-circle"></i>
                <h3>Sin datos suficientes</h3>
                <p>No se encontraron suficientes datos para comparar estas colonias.</p>
            </div>
        `;
        return;
    }
    
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = `
        <div class="comparison-header">
            <h3>Comparación de Colonias</h3>
            <p>Datos basados en propiedades activas en el mercado</p>
        </div>
        
        <div class="comparison-overview">
            ${createOverviewCards(data.neighborhoods)}
        </div>
        
        <div class="comparison-charts">
            <div class="comparison-chart-container">
                <h4>Precio Promedio</h4>
                <canvas id="avgPriceChart" width="400" height="200"></canvas>
            </div>
            <div class="comparison-chart-container">
                <h4>Precio por m²</h4>
                <canvas id="pricePerM2Chart" width="400" height="200"></canvas>
            </div>
            <div class="comparison-chart-container">
                <h4>Número de Propiedades</h4>
                <canvas id="listingCountChart" width="400" height="200"></canvas>
            </div>
            <div class="comparison-chart-container">
                <h4>Distribución por Tipo</h4>
                <canvas id="propertyTypeChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="comparison-details">
            ${createDetailedComparison(data.neighborhoods)}
        </div>
    `;
    
    // Create charts after DOM is updated
    setTimeout(() => {
        createComparisonCharts(data.neighborhoods);
    }, 100);
}

// Create overview cards
function createOverviewCards(neighborhoods) {
    return neighborhoods.map(neighborhood => `
        <div class="overview-card">
            <div class="overview-header">
                <h4>${neighborhood.colonia}</h4>
                <span class="overview-city">CDMX</span>
            </div>
            <div class="overview-stats">
                <div class="overview-stat">
                    <div class="stat-value">${formatPrice(neighborhood.avg_price_mxn || 0)}</div>
                    <div class="stat-label">Precio Promedio</div>
                </div>
                <div class="overview-stat">
                    <div class="stat-value">${formatPrice(neighborhood.avg_price_per_m2 || 0)}/m²</div>
                    <div class="stat-label">Precio por m²</div>
                </div>
                <div class="overview-stat">
                    <div class="stat-value">${neighborhood.listing_count || 0}</div>
                    <div class="stat-label">Propiedades</div>
                </div>
                <div class="overview-stat">
                    <div class="stat-value">${Math.round(neighborhood.avg_size_m2 || 0)}m²</div>
                    <div class="stat-label">Tamaño Promedio</div>
                </div>
            </div>
            ${neighborhood.market_trend ? `
                <div class="overview-trend ${neighborhood.market_trend.direction}">
                    <i class="fas fa-arrow-${neighborhood.market_trend.direction === 'up' ? 'up' : 'down'}"></i>
                    <span>${neighborhood.market_trend.direction === 'up' ? 'Al alza' : 'A la baja'}</span>
                    <small>${neighborhood.market_trend.percentage}%</small>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Create detailed comparison table
function createDetailedComparison(neighborhoods) {
    const metrics = [
        { key: 'avg_price_mxn', label: 'Precio Promedio', format: 'price' },
        { key: 'avg_price_per_m2', label: 'Precio por m²', format: 'price_per_m2' },
        { key: 'median_price_mxn', label: 'Precio Mediana', format: 'price' },
        { key: 'listing_count', label: 'Propiedades Activas', format: 'number' },
        { key: 'avg_size_m2', label: 'Tamaño Promedio', format: 'area' },
        { key: 'avg_bedrooms', label: 'Recámaras Promedio', format: 'decimal' },
        { key: 'avg_bathrooms', label: 'Baños Promedio', format: 'decimal' },
        { key: 'price_range_low', label: 'Precio Mínimo', format: 'price' },
        { key: 'price_range_high', label: 'Precio Máximo', format: 'price' }
    ];
    
    return `
        <div class="detailed-comparison">
            <h4>Comparación Detallada</h4>
            <div class="comparison-table">
                <div class="comparison-row header">
                    <div class="metric-label">Métrica</div>
                    ${neighborhoods.map(n => `<div class="neighborhood-column">${n.colonia}</div>`).join('')}
                </div>
                ${metrics.map(metric => `
                    <div class="comparison-row">
                        <div class="metric-label">${metric.label}</div>
                        ${neighborhoods.map(n => {
                            const value = n[metric.key];
                            return `<div class="metric-value">${formatMetricValue(value, metric.format)}</div>`;
                        }).join('')}
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Format metric value based on type
function formatMetricValue(value, format) {
    if (value == null || value === undefined) return 'N/A';
    
    switch (format) {
        case 'price':
            return formatPrice(value);
        case 'price_per_m2':
            return `${formatPrice(value)}/m²`;
        case 'area':
            return `${Math.round(value)}m²`;
        case 'decimal':
            return value.toFixed(1);
        case 'number':
            return value.toLocaleString('es-MX');
        default:
            return value.toString();
    }
}

// Create comparison charts
function createComparisonCharts(neighborhoods) {
    const colors = ['#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#3B82F6'];
    
    // Average Price Chart
    createBarChart('avgPriceChart', {
        labels: neighborhoods.map(n => n.colonia),
        datasets: [{
            label: 'Precio Promedio',
            data: neighborhoods.map(n => (n.avg_price_mxn || 0) / 1000000), // Convert to millions
            backgroundColor: colors.slice(0, neighborhoods.length),
            borderColor: colors.slice(0, neighborhoods.length),
            borderWidth: 1
        }]
    }, {
        title: 'Precio Promedio (Millones MXN)',
        yAxisFormat: (value) => `$${value.toFixed(1)}M`
    });
    
    // Price per m² Chart
    createBarChart('pricePerM2Chart', {
        labels: neighborhoods.map(n => n.colonia),
        datasets: [{
            label: 'Precio por m²',
            data: neighborhoods.map(n => (n.avg_price_per_m2 || 0) / 1000), // Convert to thousands
            backgroundColor: colors.slice(0, neighborhoods.length),
            borderColor: colors.slice(0, neighborhoods.length),
            borderWidth: 1
        }]
    }, {
        title: 'Precio por m² (Miles MXN)',
        yAxisFormat: (value) => `$${value.toFixed(0)}k`
    });
    
    // Listing Count Chart
    createBarChart('listingCountChart', {
        labels: neighborhoods.map(n => n.colonia),
        datasets: [{
            label: 'Propiedades',
            data: neighborhoods.map(n => n.listing_count || 0),
            backgroundColor: colors.slice(0, neighborhoods.length),
            borderColor: colors.slice(0, neighborhoods.length),
            borderWidth: 1
        }]
    }, {
        title: 'Número de Propiedades',
        yAxisFormat: (value) => value.toString()
    });
    
    // Property Type Distribution Chart
    if (neighborhoods[0]?.property_types) {
        createPropertyTypeChart('propertyTypeChart', neighborhoods);
    }
}

// Create bar chart
function createBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#f3f4f6',
                    bodyColor: '#e5e7eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            if (options.yAxisFormat) {
                                return options.yAxisFormat(context.parsed.y);
                            }
                            return context.parsed.y.toLocaleString('es-MX');
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: '#374151' },
                    ticks: { color: '#9CA3AF' }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#374151' },
                    ticks: {
                        color: '#9CA3AF',
                        callback: options.yAxisFormat || function(value) {
                            return value.toLocaleString('es-MX');
                        }
                    }
                }
            }
        }
    });
}

// Create property type distribution chart
function createPropertyTypeChart(canvasId, neighborhoods) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Aggregate property types across neighborhoods
    const allTypes = new Set();
    neighborhoods.forEach(n => {
        if (n.property_types) {
            Object.keys(n.property_types).forEach(type => allTypes.add(type));
        }
    });
    
    const typeArray = Array.from(allTypes);
    const colors = ['#8B5CF6', '#10B981', '#F59E0B', '#EF4444', '#3B82F6'];
    
    const datasets = neighborhoods.map((neighborhood, index) => ({
        label: neighborhood.colonia,
        data: typeArray.map(type => neighborhood.property_types?.[type] || 0),
        backgroundColor: colors[index % colors.length],
        borderColor: colors[index % colors.length],
        borderWidth: 1
    }));
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: typeArray,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#e5e7eb',
                        usePointStyle: true
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
                    beginAtZero: true,
                    grid: { color: '#374151' },
                    ticks: {
                        color: '#9CA3AF',
                        callback: function(value) {
                            return value.toString();
                        }
                    }
                }
            }
        }
    });
}

// Close neighborhood modal
function closeNeighborhoodModal() {
    const modal = document.getElementById('neighborhoodModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Generate neighborhood insights
function generateNeighborhoodInsights(neighborhoods) {
    const insights = [];
    
    if (neighborhoods.length >= 2) {
        const sortedByPrice = [...neighborhoods].sort((a, b) => (b.avg_price_mxn || 0) - (a.avg_price_mxn || 0));
        const mostExpensive = sortedByPrice[0];
        const leastExpensive = sortedByPrice[sortedByPrice.length - 1];
        
        if (mostExpensive.colonia !== leastExpensive.colonia) {
            const priceDiff = ((mostExpensive.avg_price_mxn - leastExpensive.avg_price_mxn) / leastExpensive.avg_price_mxn * 100).toFixed(0);
            insights.push(`${mostExpensive.colonia} es ${priceDiff}% más caro que ${leastExpensive.colonia}`);
        }
        
        const sortedByValue = [...neighborhoods].sort((a, b) => (a.avg_price_per_m2 || 0) - (b.avg_price_per_m2 || 0));
        const bestValue = sortedByValue[0];
        insights.push(`${bestValue.colonia} tiene el mejor precio por m² (${formatPrice(bestValue.avg_price_per_m2)}/m²)`);
        
        const sortedByInventory = [...neighborhoods].sort((a, b) => (b.listing_count || 0) - (a.listing_count || 0));
        const mostInventory = sortedByInventory[0];
        if (mostInventory.listing_count > 0) {
            insights.push(`${mostInventory.colonia} tiene la mayor oferta con ${mostInventory.listing_count} propiedades`);
        }
    }
    
    return insights;
}

// Display insights
function displayInsights(insights) {
    if (insights.length === 0) return '';
    
    return `
        <div class="comparison-insights">
            <h4>Insights</h4>
            <ul>
                ${insights.map(insight => `<li>${insight}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Export functions
if (typeof window !== 'undefined') {
    window.performNeighborhoodComparison = performNeighborhoodComparison;
    window.closeNeighborhoodModal = closeNeighborhoodModal;
}