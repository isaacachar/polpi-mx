#!/usr/bin/env python3
"""Production-grade FastAPI server for Polpi MX"""

from fastapi import FastAPI, HTTPException, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import time
from database import PolpiDB
from price_intelligence import PriceIntelligence
from config import config
from url_analyzer import URLAnalyzer
from zoning_lookup import SEDUVIZoningLookup
from geocoding import CDMXGeocoder, parse_input

# Configure logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Polpi MX API",
    description="Mexican Real Estate Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and intelligence
db = PolpiDB()
intel = PriceIntelligence()
url_analyzer = URLAnalyzer()
zoning_lookup = SEDUVIZoningLookup(use_mock_data=True)
geocoder = CDMXGeocoder()

# Pydantic models for request/response validation
class ListingFilters(BaseModel):
    city: Optional[str] = None
    colonia: Optional[str] = None
    property_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=config.DEFAULT_PAGE_SIZE, ge=1, le=config.MAX_PAGE_SIZE)

class ListingResponse(BaseModel):
    id: str
    title: Optional[str]
    price_mxn: Optional[float]
    price_usd: Optional[float]
    property_type: Optional[str]
    city: Optional[str]
    colonia: Optional[str]
    size_m2: Optional[float]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    price_per_m2: Optional[float]
    data_quality_score: Optional[float]

class PaginatedListingsResponse(BaseModel):
    listings: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class StatsResponse(BaseModel):
    total_listings: int
    cities: int
    colonias: int
    sources: Dict[str, int]
    property_types: List[Dict[str, Any]]

class CityStats(BaseModel):
    city: str
    listing_count: int
    avg_price: Optional[float]
    avg_price_per_m2: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]

class InvestmentAnalysis(BaseModel):
    listing_id: str
    purchase_price: float
    estimated_yield: float
    monthly_rental: float
    annual_rental: float
    cap_rate: float
    investment_grade: str

class URLAnalysisRequest(BaseModel):
    url: str = Field(..., description="Property listing URL to analyze")

class URLAnalysisResponse(BaseModel):
    property: Dict[str, Any]
    zoning: Optional[Dict[str, Any]]
    buildable: Optional[Dict[str, Any]]
    comparables: List[Dict[str, Any]]
    analysis: Dict[str, Any]

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.client.host} - {request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.3f}s"
    )
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc) if config.DEBUG else None}
    )

# API v1 endpoints
@app.get(f"{config.API_V1_PREFIX}/listings", response_model=PaginatedListingsResponse)
async def get_listings_v1(
    page: int = Query(1, ge=1),
    per_page: int = Query(config.DEFAULT_PAGE_SIZE, ge=1, le=config.MAX_PAGE_SIZE),
    sort_by: str = Query("newest", pattern="^(newest|price|price_desc|size|price_per_m2|deal_score)$"),
    city: Optional[str] = Query(None),
    colonia: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    bedrooms: Optional[int] = Query(None, ge=0),
    bathrooms: Optional[int] = Query(None, ge=0),
    min_size: Optional[float] = Query(None, ge=0),
    max_size: Optional[float] = Query(None, ge=0)
):
    """Get paginated listings with filters and sorting"""
    filters = {}
    if city: filters['city'] = city
    if colonia: filters['colonia'] = colonia
    if property_type: filters['property_type'] = property_type
    if min_price: filters['min_price'] = min_price
    if max_price: filters['max_price'] = max_price
    if bedrooms: filters['bedrooms'] = bedrooms
    if bathrooms: filters['bathrooms'] = bathrooms
    if min_size: filters['min_size'] = min_size
    if max_size: filters['max_size'] = max_size
    
    result = db.get_listings_paginated(filters, page, per_page, sort_by)
    return result

@app.get(f"{config.API_V1_PREFIX}/listings/{{listing_id}}")
async def get_listing_detail(listing_id: str = Path(..., description="Listing ID")):
    """Get single listing with full analysis"""
    # Get basic listing data
    listings = db.get_listings(limit=10000)
    listing = next((l for l in listings if l['id'] == listing_id), None)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Add enhanced analysis
    analysis = intel.analyze_listing(listing_id)
    
    # Merge listing data with analysis
    listing.update({
        'deal_score': analysis.get('deal_score'),
        'deal_breakdown': analysis.get('deal_breakdown'),
        'neighborhood_stats': analysis.get('neighborhood_stats'),
        'comparables': analysis.get('comparables'),
        'recommendation': analysis.get('recommendation')
    })
    
    return listing

@app.get(f"{config.API_V1_PREFIX}/stats", response_model=StatsResponse)
async def get_platform_stats():
    """Get platform statistics"""
    stats = db.get_stats()
    return stats

@app.get(f"{config.API_V1_PREFIX}/cities")
async def get_cities():
    """Get cities with counts and average prices"""
    cities = db.get_cities_with_stats()
    return cities

@app.get(f"{config.API_V1_PREFIX}/cities/{{city}}/overview")
async def get_city_overview(city: str = Path(..., description="City name")):
    """Get city market overview with detailed statistics"""
    overview = intel.get_city_overview(city)
    return overview

@app.get(f"{config.API_V1_PREFIX}/neighborhoods/compare")
async def compare_neighborhoods(
    colonias: str = Query(..., description="Comma-separated list of 2-3 neighborhoods"),
    city: Optional[str] = Query(None, description="City name (auto-detected if not provided)")
):
    """Compare 2-3 neighborhoods side by side"""
    colonia_list = [c.strip() for c in colonias.split(',') if c.strip()]
    
    if len(colonia_list) < 2 or len(colonia_list) > 3:
        raise HTTPException(
            status_code=400, 
            detail="Must provide between 2 and 3 neighborhoods to compare"
        )
    
    comparison = intel.compare_neighborhoods(colonia_list, city)
    
    if 'error' in comparison:
        raise HTTPException(status_code=400, detail=comparison['error'])
    
    return comparison

@app.get(f"{config.API_V1_PREFIX}/market/trends")
async def get_market_trends(
    city: str = Query(..., description="City name"),
    property_type: Optional[str] = Query(None, description="Property type filter"),
    months: int = Query(12, ge=1, le=24, description="Number of months of historical data")
):
    """Get price trends by city with historical data"""
    trends = intel.generate_price_trends(city, property_type)
    
    if not trends:
        raise HTTPException(
            status_code=404, 
            detail=f"No trend data available for {city}"
        )
    
    return {
        'city': city,
        'property_type': property_type,
        'months_requested': months,
        'trends': trends[:months]
    }

@app.get(f"{config.API_V1_PREFIX}/listings/{{listing_id}}/investment")
async def get_investment_analysis(listing_id: str = Path(..., description="Listing ID")):
    """Get comprehensive investment analysis"""
    analysis = intel.get_investment_analysis(listing_id)
    
    if 'error' in analysis:
        raise HTTPException(status_code=404, detail=analysis['error'])
    
    return analysis

@app.get(f"{config.API_V1_PREFIX}/listings/{{listing_id}}/report")
async def generate_listing_report(listing_id: str = Path(..., description="Listing ID")):
    """Generate comprehensive listing report data (JSON that frontend can render)"""
    # Get listing details
    listing_detail = await get_listing_detail(listing_id)
    
    # Get investment analysis
    investment = intel.get_investment_analysis(listing_id)
    
    # Combine into comprehensive report
    report = {
        'listing': listing_detail,
        'investment_analysis': investment if 'error' not in investment else None,
        'generated_at': time.time(),
        'report_sections': {
            'property_overview': True,
            'market_analysis': True,
            'investment_projections': 'error' not in investment,
            'comparable_properties': len(listing_detail.get('comparables', [])) > 0,
            'neighborhood_insights': listing_detail.get('neighborhood_stats') is not None
        }
    }
    
    return report

@app.get(f"{config.API_V1_PREFIX}/search")
async def search_listings(
    q: str = Query(..., min_length=config.SEARCH_MIN_LENGTH, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(config.DEFAULT_PAGE_SIZE, ge=1, le=config.MAX_PAGE_SIZE)
):
    """Full-text search across listings"""
    results = db.search_listings(q, page, per_page)
    return results

@app.post(f"{config.API_V1_PREFIX}/analyze-url", response_model=URLAnalysisResponse)
async def analyze_url(request: URLAnalysisRequest):
    """
    Analyze a property listing URL and get instant market intelligence.
    
    Extracts property data, zoning information, buildable area calculations,
    and comparable listings from the database.
    """
    try:
        # Step 1: Extract property data from URL
        logger.info(f"Analyzing URL: {request.url}")
        property_data = url_analyzer.analyze_url(request.url)
        
        if not property_data:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract property data from URL"
            )
        
        # Convert to dict for response
        property_dict = property_data.to_dict()
        
        # Step 2: Get zoning information (if coordinates available)
        zoning_info = None
        buildable_info = None
        
        if property_data.lat and property_data.lng:
            try:
                zoning = zoning_lookup.lookup_by_coordinates(
                    property_data.lat,
                    property_data.lng
                )
                if zoning:
                    zoning_info = {
                        'category': zoning.category,
                        'category_full': zoning.category_full,
                        'max_floors': zoning.max_floors,
                        'max_cos': zoning.max_cos,
                        'max_cus': zoning.max_cus,
                        'allowed_uses': zoning.allowed_uses,
                        'min_open_area_pct': zoning.min_open_area_pct,
                        'is_heritage_zone': zoning.is_heritage_zone
                    }
                    
                    # Step 3: Calculate buildable area
                    if property_data.lot_size_m2 or property_data.size_m2:
                        lot_size = property_data.lot_size_m2 or property_data.size_m2
                        buildable_info = zoning_lookup.calculate_buildable_area(
                            lot_size,
                            zoning
                        )
                        
                        # Add price per buildable m²
                        if property_data.price_mxn and buildable_info.get('max_total_construction_m2'):
                            buildable_info['price_per_buildable_m2'] = round(
                                property_data.price_mxn / buildable_info['max_total_construction_m2'],
                                2
                            )
                            
            except Exception as e:
                logger.warning(f"Zoning lookup failed: {e}")
        
        # Step 4: Find comparable listings from database
        comparables = []
        if property_data.colonia:
            try:
                # Get listings from same colonia
                filters = {'colonia': property_data.colonia}
                if property_data.property_type:
                    filters['property_type'] = property_data.property_type
                
                result = db.get_listings_paginated(filters, page=1, per_page=10, sort_by='newest')
                comparables = result['listings'][:5]  # Top 5 comps
                
            except Exception as e:
                logger.warning(f"Comparables lookup failed: {e}")
        
        # Step 5: Calculate analysis metrics
        analysis = {
            'data_quality': 'good' if all([
                property_data.price_mxn,
                property_data.size_m2,
                property_data.colonia
            ]) else 'partial',
            'has_zoning_data': zoning_info is not None,
            'has_comparables': len(comparables) > 0,
            'comparable_count': len(comparables)
        }
        
        # Add market positioning if we have comps
        if comparables and property_data.price_mxn and property_data.size_m2:
            comp_prices_per_m2 = [
                c['price_mxn'] / c['size_m2'] 
                for c in comparables 
                if c.get('price_mxn') and c.get('size_m2') and c['size_m2'] > 0
            ]
            
            if comp_prices_per_m2:
                avg_comp_price = sum(comp_prices_per_m2) / len(comp_prices_per_m2)
                listing_price_per_m2 = property_data.price_mxn / property_data.size_m2
                
                analysis['avg_market_price_per_m2'] = round(avg_comp_price, 2)
                analysis['listing_price_per_m2'] = round(listing_price_per_m2, 2)
                analysis['price_vs_market_pct'] = round(
                    ((listing_price_per_m2 - avg_comp_price) / avg_comp_price) * 100,
                    1
                )
                
                if analysis['price_vs_market_pct'] < -15:
                    analysis['market_position'] = 'Below Market (Potential Deal)'
                elif analysis['price_vs_market_pct'] > 15:
                    analysis['market_position'] = 'Above Market'
                else:
                    analysis['market_position'] = 'Market Rate'
        
        # Build response
        response = {
            'property': property_dict,
            'zoning': zoning_info,
            'buildable': buildable_info,
            'comparables': comparables,
            'analysis': analysis
        }
        
        logger.info(f"Analysis complete for {request.url}")
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

class LocationAnalysisRequest(BaseModel):
    location: str = Field(..., description="Address, colonia name, or coordinates (lat,lng)")
    lot_size_m2: Optional[float] = Field(None, description="Lot size in m² for buildable calculations")

class LocationAnalysisResponse(BaseModel):
    location: Dict[str, Any]
    zoning: Optional[Dict[str, Any]]
    buildable: Optional[Dict[str, Any]]
    development_potential: Optional[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]]
    comparables: List[Dict[str, Any]]

@app.post(f"{config.API_V1_PREFIX}/analyze-location", response_model=LocationAnalysisResponse)
async def analyze_location(request: LocationAnalysisRequest):
    """
    Analyze a location by address, colonia, or coordinates.
    Get zoning information, buildable potential, and market intelligence.
    
    NO SCRAPING - uses public data sources only.
    """
    try:
        logger.info(f"Analyzing location: {request.location}")
        
        # Step 1: Parse input and get coordinates
        address_input, coords = parse_input(request.location)
        
        geo_result = None
        lat, lng = None, None
        colonia = None
        
        if coords:
            # User provided coordinates
            lat, lng = coords
            # Reverse geocode to get address info
            geo_result = geocoder.reverse_geocode(lat, lng)
        elif address_input:
            # User provided address or colonia
            geo_result = geocoder.geocode_address(address_input)
            if not geo_result:
                # Try as colonia search
                geo_result = geocoder.search_colonia(address_input)
        
        if not geo_result:
            raise HTTPException(
                status_code=404,
                detail=f"Could not geocode location: {request.location}"
            )
        
        lat, lng = geo_result.lat, geo_result.lng
        colonia = geo_result.colonia
        
        location_info = {
            'lat': lat,
            'lng': lng,
            'address': geo_result.address,
            'colonia': geo_result.colonia,
            'delegacion': geo_result.delegacion,
            'city': geo_result.city,
            'display_name': geo_result.display_name
        }
        
        # Step 2: Get zoning information
        zoning_info = None
        buildable_info = None
        development_potential = None
        
        try:
            zoning = zoning_lookup.lookup_by_coordinates(lat, lng)
            if zoning:
                zoning_info = {
                    'category': zoning.category,
                    'category_full': zoning.category_full,
                    'max_floors': zoning.max_floors,
                    'max_cos': zoning.max_cos,
                    'max_cus': zoning.max_cus,
                    'allowed_uses': zoning.allowed_uses,
                    'min_open_area_pct': zoning.min_open_area_pct,
                    'is_heritage_zone': zoning.is_heritage_zone
                }
                
                # Step 3: Calculate buildable area if lot size provided
                if request.lot_size_m2:
                    buildable_info = zoning_lookup.calculate_buildable_area(
                        request.lot_size_m2,
                        zoning
                    )
                    
                    # Calculate development potential
                    max_construction = buildable_info.get('max_total_construction_m2', 0)
                    
                    # Estimate unit counts (rough heuristics)
                    development_potential = {
                        'lot_size_m2': request.lot_size_m2,
                        'max_buildable_m2': max_construction,
                        'estimated_units': {}
                    }
                    
                    # Apartment estimates (assuming 60-80m² per unit)
                    if max_construction > 0:
                        development_potential['estimated_units']['apartments_60m2'] = int(max_construction / 60)
                        development_potential['estimated_units']['apartments_80m2'] = int(max_construction / 80)
                        development_potential['estimated_units']['hotel_rooms_35m2'] = int(max_construction / 35)
                        development_potential['estimated_units']['office_space_usable'] = int(max_construction * 0.85)  # 85% efficiency
                    
        except Exception as e:
            logger.warning(f"Zoning lookup failed: {e}")
        
        # Step 4: Get market data from database
        market_data = None
        comparables = []
        
        if colonia:
            try:
                # Get all listings in this colonia
                filters = {'colonia': colonia}
                result = db.get_listings_paginated(filters, page=1, per_page=50, sort_by='newest')
                all_listings = result['listings']
                
                if all_listings:
                    # Calculate market averages
                    prices_per_m2 = [
                        l['price_mxn'] / l['size_m2']
                        for l in all_listings
                        if l.get('price_mxn') and l.get('size_m2') and l['size_m2'] > 0
                    ]
                    
                    if prices_per_m2:
                        market_data = {
                            'colonia': colonia,
                            'total_listings': len(all_listings),
                            'avg_price_per_m2': round(sum(prices_per_m2) / len(prices_per_m2), 2),
                            'min_price_per_m2': round(min(prices_per_m2), 2),
                            'max_price_per_m2': round(max(prices_per_m2), 2),
                        }
                        
                        # Calculate price per buildable m² if we have buildable info
                        if buildable_info and buildable_info.get('max_total_construction_m2'):
                            avg_land_price_per_buildable = market_data['avg_price_per_m2'] * (
                                request.lot_size_m2 / buildable_info['max_total_construction_m2']
                            ) if request.lot_size_m2 else None
                            
                            if avg_land_price_per_buildable:
                                market_data['avg_land_price_per_buildable_m2'] = round(avg_land_price_per_buildable, 2)
                    
                    # Get top 5 comparables
                    comparables = all_listings[:5]
                    
            except Exception as e:
                logger.warning(f"Market data lookup failed: {e}")
        
        # Build response
        response = {
            'location': location_info,
            'zoning': zoning_info,
            'buildable': buildable_info,
            'development_potential': development_potential,
            'market_data': market_data,
            'comparables': comparables
        }
        
        logger.info(f"Location analysis complete for {request.location}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Location analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

# Legacy API endpoints for backward compatibility
@app.get("/api/listings")
async def get_listings_legacy(
    limit: int = Query(100, le=config.MAX_PAGE_SIZE),
    city: Optional[str] = Query(None),
    colonia: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[int] = Query(None),
    min_size: Optional[float] = Query(None),
    max_size: Optional[float] = Query(None)
):
    """Legacy endpoint - redirects to new paginated API"""
    filters = {}
    if city: filters['city'] = city
    if colonia: filters['colonia'] = colonia
    if property_type: filters['property_type'] = property_type
    if min_price: filters['min_price'] = min_price
    if max_price: filters['max_price'] = max_price
    if bedrooms: filters['bedrooms'] = bedrooms
    if bathrooms: filters['bathrooms'] = bathrooms
    if min_size: filters['min_size'] = min_size
    if max_size: filters['max_size'] = max_size
    
    result = db.get_listings_paginated(filters, page=1, per_page=limit)
    return result['listings']

@app.get("/api/stats")
async def get_stats_legacy():
    """Legacy stats endpoint"""
    return await get_platform_stats()

@app.get("/api/listing/{listing_id}")
async def get_listing_legacy(listing_id: str):
    """Legacy listing detail endpoint"""
    return await get_listing_detail(listing_id)

@app.get("/api/analyze/{listing_id}")
async def analyze_listing_legacy(listing_id: str):
    """Legacy analysis endpoint"""
    analysis = intel.analyze_listing(listing_id)
    if 'error' in analysis:
        raise HTTPException(status_code=404, detail=analysis['error'])
    return analysis

@app.get("/api/cities")
async def get_cities_legacy():
    """Legacy cities endpoint"""
    return await get_cities()

@app.get("/api/city-overview")
async def city_overview_legacy(city: str = Query(...)):
    """Legacy city overview endpoint"""
    return await get_city_overview(city)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - serves the main application"""
    try:
        # Try to serve index.html from static files
        with open(f"{config.STATIC_DIR}/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return {
            "message": "Polpi MX API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health"
        }

# Mount static files (CSS, JS, images)
try:
    app.mount("/css", StaticFiles(directory=f"{config.STATIC_DIR}/css"), name="css")
    app.mount("/js", StaticFiles(directory=f"{config.STATIC_DIR}/js"), name="js")
    app.mount("/images", StaticFiles(directory=f"{config.STATIC_DIR}/images"), name="images")
    logger.info(f"Static files mounted from {config.STATIC_DIR}")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Add a catch-all static file handler for the web directory
@app.get("/{file_path:path}")
async def serve_static_files(file_path: str):
    """Serve static files from web directory"""
    try:
        # Security check - prevent directory traversal
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=404, detail="File not found")
        
        file_full_path = f"{config.STATIC_DIR}/{file_path}"
        
        with open(file_full_path, "rb") as f:
            content = f.read()
        
        # Determine content type
        content_type = "text/html"
        if file_path.endswith(".css"):
            content_type = "text/css"
        elif file_path.endswith(".js"):
            content_type = "application/javascript"
        elif file_path.endswith(".json"):
            content_type = "application/json"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            content_type = "image/jpeg"
        
        if content_type == "text/html":
            return HTMLResponse(content=content.decode('utf-8'))
        elif content_type.startswith('text') or content_type == 'application/json':
            return Response(content=content, media_type=content_type)
        else:
            return Response(content=content, media_type=content_type)
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

# Main execution
if __name__ == "__main__":
    import uvicorn
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                      POLPI MX 2.0                       ║
║            Mexican Real Estate Intelligence              ║
║                  FastAPI Production Server               ║
╚══════════════════════════════════════════════════════════╝

🚀 Server starting at: http://{config.HOST}:{config.PORT}
📊 API Documentation: http://{config.HOST}:{config.PORT}/docs  
📋 ReDoc: http://{config.HOST}:{config.PORT}/redoc
💓 Health Check: http://{config.HOST}:{config.PORT}/health

🔧 Configuration:
   - Debug Mode: {config.DEBUG}
   - Database: {config.DB_PATH}
   - Static Files: {config.STATIC_DIR}
   - CORS Origins: {len(config.CORS_ORIGINS)} configured

Press Ctrl+C to stop the server
""")
    
    uvicorn.run(
        "api_server:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        access_log=True
    )