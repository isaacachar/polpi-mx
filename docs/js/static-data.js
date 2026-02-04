// Static data for GitHub Pages deployment
// This file contains embedded data to replace API calls

// Load the data files
const STATIC_LISTINGS = fetch('js/data-listings.json').then(r => r.json());
const STATIC_STATS = fetch('js/data-stats.json').then(r => r.json());

// Override fetchWithFallback to return embedded data
const originalFetchWithFallback = window.fetchWithFallback;
window.fetchWithFallback = async function(v1Url, fallbackUrl) {
    const url = v1Url || fallbackUrl;
    
    // Stats endpoint
    if (url.includes('/stats')) {
        return {
            ok: true,
            json: async () => await STATIC_STATS
        };
    }
    
    // Listings endpoint
    if (url.includes('/listings')) {
        const listings = await STATIC_LISTINGS;
        const urlParams = new URLSearchParams(url.split('?')[1]);
        
        let filtered = [...listings];
        
        // Apply filters
        if (urlParams.has('colonia')) {
            const colonia = urlParams.get('colonia');
            filtered = filtered.filter(l => l.colonia === colonia);
        }
        
        if (urlParams.has('property_type')) {
            const type = urlParams.get('property_type');
            filtered = filtered.filter(l => 
                l.property_type && l.property_type.toLowerCase().includes(type.toLowerCase())
            );
        }
        
        if (urlParams.has('min_price')) {
            const minPrice = parseFloat(urlParams.get('min_price'));
            filtered = filtered.filter(l => l.price_mxn >= minPrice);
        }
        
        if (urlParams.has('max_price')) {
            const maxPrice = parseFloat(urlParams.get('max_price'));
            filtered = filtered.filter(l => l.price_mxn <= maxPrice);
        }
        
        if (urlParams.has('bedrooms')) {
            const bedrooms = parseInt(urlParams.get('bedrooms'));
            filtered = filtered.filter(l => l.bedrooms >= bedrooms);
        }
        
        if (urlParams.has('bathrooms')) {
            const bathrooms = parseInt(urlParams.get('bathrooms'));
            filtered = filtered.filter(l => l.bathrooms >= bathrooms);
        }
        
        if (urlParams.has('min_size')) {
            const minSize = parseFloat(urlParams.get('min_size'));
            filtered = filtered.filter(l => l.size_m2 >= minSize);
        }
        
        if (urlParams.has('max_size')) {
            const maxSize = parseFloat(urlParams.get('max_size'));
            filtered = filtered.filter(l => l.size_m2 <= maxSize);
        }
        
        if (urlParams.has('search')) {
            const search = urlParams.get('search').toLowerCase();
            filtered = filtered.filter(l => 
                (l.title && l.title.toLowerCase().includes(search)) ||
                (l.colonia && l.colonia.toLowerCase().includes(search)) ||
                (l.property_type && l.property_type.toLowerCase().includes(search)) ||
                (l.description && l.description.toLowerCase().includes(search))
            );
        }
        
        return {
            ok: true,
            json: async () => filtered
        };
    }
    
    // Colonias endpoint
    if (url.includes('/colonias')) {
        const listings = await STATIC_LISTINGS;
        const coloniasMap = {};
        
        listings.forEach(listing => {
            if (listing.colonia) {
                coloniasMap[listing.colonia] = (coloniasMap[listing.colonia] || 0) + 1;
            }
        });
        
        const colonias = Object.entries(coloniasMap)
            .map(([colonia, count]) => ({ colonia, count }))
            .sort((a, b) => b.count - a.count);
        
        return {
            ok: true,
            json: async () => colonias
        };
    }
    
    // Individual listing endpoint
    if (url.match(/\/listing\/[^/]+$/)) {
        const listingId = url.split('/').pop();
        const listings = await STATIC_LISTINGS;
        const listing = listings.find(l => l.id === listingId);
        
        return {
            ok: true,
            json: async () => listing || {}
        };
    }
    
    // Analysis endpoint - return mock data
    if (url.includes('/analyze/')) {
        const listingId = url.split('/').pop().split('?')[0];
        const listings = await STATIC_LISTINGS;
        const listing = listings.find(l => l.id === listingId);
        
        if (listing) {
            // Generate mock analysis data
            const dealScore = calculateDealScore(listing);
            const comparables = listings
                .filter(l => 
                    l.id !== listingId &&
                    l.colonia === listing.colonia &&
                    Math.abs((l.price_mxn || 0) - (listing.price_mxn || 0)) < (listing.price_mxn || 0) * 0.3
                )
                .slice(0, 5);
            
            return {
                ok: true,
                json: async () => ({
                    deal_score: dealScore,
                    comparables: comparables,
                    market_avg_price: listing.price_per_m2 ? listing.price_per_m2 * 1.1 : null,
                    price_vs_market: listing.price_per_m2 ? -10 : 0
                })
            };
        }
        
        return {
            ok: true,
            json: async () => ({ deal_score: 50, comparables: [] })
        };
    }
    
    // Neighborhood stats - return mock data
    if (url.includes('/neighborhood/')) {
        const colonia = decodeURIComponent(url.split('/neighborhood/')[1].split('?')[0]);
        const listings = await STATIC_LISTINGS;
        const coloniaListings = listings.filter(l => l.colonia === colonia);
        
        const avgPrice = coloniaListings.length > 0
            ? coloniaListings.reduce((sum, l) => sum + (l.price_mxn || 0), 0) / coloniaListings.length
            : 0;
        
        const avgPricePerM2 = coloniaListings.length > 0
            ? coloniaListings.reduce((sum, l) => sum + (l.price_per_m2 || 0), 0) / coloniaListings.length
            : 0;
        
        return {
            ok: true,
            json: async () => ({
                colonia: colonia,
                total_listings: coloniaListings.length,
                avg_price: avgPrice,
                avg_price_per_m2: avgPricePerM2,
                property_types: {}
            })
        };
    }
    
    // Trends endpoint - return mock data
    if (url.includes('/trends')) {
        return {
            ok: true,
            json: async () => ({
                monthly_trends: [],
                price_changes: []
            })
        };
    }
    
    // Default: try to fetch normally (will fail gracefully)
    console.warn('Unhandled static endpoint:', url);
    return {
        ok: false,
        json: async () => ({})
    };
};

console.log('Static data module loaded for GitHub Pages');
