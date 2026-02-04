# 🐙 Polpi MX - Mexican Real Estate Intelligence Platform

A working prototype of a Zillow-like platform for the Mexican real estate market, featuring data aggregation, price intelligence, and neighborhood analytics.

## What This Is

Polpi MX solves the real estate data fragmentation problem in Mexico by:
- **Aggregating** listings from multiple sources (Inmuebles24, Vivanuncios, Century21)
- **Analyzing** prices with comparable properties and neighborhood statistics
- **Visualizing** properties on an interactive map with price heatmaps
- **Providing** deal scores and price anomaly detection

## Features

### ✅ Working in This Prototype

- **3 Working Scrapers:** Inmuebles24, Vivanuncios, Century21 (with fallback to sample data)
- **Data Pipeline:** Normalization, deduplication, geocoding
- **SQLite Database:** Listings, price history, neighborhood stats
- **Price Intelligence Engine:**
  - Comparable property analysis
  - Price per m² calculations
  - Deal score (0-100)
  - Anomaly detection (overpriced vs. potential deals)
  - Neighborhood statistics
- **Web Interface:**
  - Interactive map with clustered markers
  - Filter by city, type, price, bedrooms, bathrooms, size
  - Listing cards with photos and details
  - Modal detail view with price analysis
  - Mobile responsive

### 🚧 Production Needs (Not in Prototype)

See `ARCHITECTURE.md` for full details:
- PostgreSQL + PostGIS for spatial queries
- More scraping sources + anti-blocking infrastructure
- Historical price tracking over time
- INEGI demographic data integration
- Crime and safety data overlay
- User accounts and saved searches
- Price alerts (email/push notifications)
- Agent dashboard and API
- Mobile apps (iOS/Android)

## Quick Start

### 1. Install Dependencies

```bash
cd ~/Desktop/polpi-mx
pip3 install -r requirements.txt
```

Required packages:
- `beautifulsoup4` - HTML parsing for scrapers
- `requests` - HTTP requests
- `geopy` - Geocoding (OpenStreetMap Nominatim)
- `python-dateutil` - Date parsing

### 2. Run the Scrapers

**Quick mode** (1 page per source, ~30 listings, ~1 min):
```bash
python3 run_scrapers.py --quick
```

**Full mode** (2 pages per source, ~60 listings, ~3-5 min):
```bash
python3 run_scrapers.py
```

This will:
- Scrape listings from 3 sources
- Normalize and geocode data
- Store in `data/polpi.db` SQLite database
- Generate `data/scrape_summary.json`

**Note:** Real websites may block scraping or change structure. The scrapers include sample data generators as fallbacks so the system works regardless.

### 3. Start the Web Server

```bash
python3 api_server.py
```

Server runs at: **http://localhost:8000**

### 4. Open in Browser

Navigate to: **http://localhost:8000**

You'll see:
- Map view with property markers (color-coded by price/m²)
- Listing grid with photos and details
- Filters (city, type, price, beds, baths, size)
- Click any listing for full analysis

## Project Structure

```
polpi-mx/
├── README.md                  # This file
├── ARCHITECTURE.md            # System design, scaling, growth strategy
├── requirements.txt           # Python dependencies
├── database.py               # Database schema and operations
├── price_intelligence.py      # Price analysis engine
├── api_server.py             # HTTP API server
├── run_scrapers.py           # Main scraper orchestrator
├── scrapers/
│   ├── base_scraper.py       # Base class with common utilities
│   ├── inmuebles24_scraper.py
│   ├── vivanuncios_scraper.py
│   └── century21_scraper.py
├── web/
│   ├── index.html            # Main UI
│   ├── css/
│   │   └── style.css         # Polpi aesthetic styling
│   └── js/
│       └── app.js            # Frontend logic
└── data/
    ├── polpi.db              # SQLite database (created on first run)
    ├── scrape_summary.json   # Scraping results
    ├── raw/                  # Raw scraped JSON (debugging)
    └── html/                 # Raw HTML (debugging)
```

## API Endpoints

The API server (`api_server.py`) provides:

### Listings
- `GET /api/listings` - Search listings with filters
  - Query params: `city`, `property_type`, `min_price`, `max_price`, `bedrooms`, `bathrooms`, `min_size`, `max_size`, `limit`
- `GET /api/listing/{id}` - Get single listing with comparables
- `GET /api/analyze/{id}` - Get price intelligence analysis

### Statistics
- `GET /api/stats` - Database stats (total listings, cities, sources)
- `GET /api/cities` - List of cities with listing counts
- `GET /api/city-overview?city={name}` - City-level price overview

### Examples

```bash
# Get all listings in Ciudad de México
curl "http://localhost:8000/api/listings?city=Ciudad+de+México"

# Get departamentos under $5M with 2+ bedrooms
curl "http://localhost:8000/api/listings?property_type=departamento&max_price=5000000&bedrooms=2"

# Get analysis for a specific listing
curl "http://localhost:8000/api/analyze/abc123def456"
```

## Database Schema

### `listings` table
Core listing data:
- Identification: `id`, `source`, `source_id`, `url`
- Pricing: `price_mxn`, `price_usd`
- Property: `property_type`, `bedrooms`, `bathrooms`, `size_m2`, `lot_size_m2`
- Location: `state`, `city`, `colonia`, `lat`, `lng`
- Details: `title`, `description`, `images`, `amenities`, `parking_spaces`
- Agent: `agent_name`, `agent_phone`
- Metadata: `scraped_date`, `listed_date`, `data_quality_score`, `raw_data`

### `price_history` table
Tracks price changes over time (for trend detection)

### `neighborhood_stats` table
Cached statistics by city/colonia/property_type

### `duplicates` table
Links duplicate listings across sources

## How It Works

### Data Acquisition

1. **Scrapers** fetch listing pages from Mexican real estate sites
2. **Parser** extracts structured data (price, location, features)
3. **Normalizer** converts to unified schema
4. **Geocoder** adds lat/lng using OpenStreetMap Nominatim
5. **Deduplicator** identifies same property across multiple sources
6. **Quality scorer** rates data completeness (0-1)

### Price Intelligence

For each listing, the engine:

1. **Finds comparables** - Similar properties (same city/colonia, similar size, same type)
2. **Calculates price per m²** - Normalizes for size
3. **Gets neighborhood stats** - Average price, price/m², listing count
4. **Generates deal score** (0-100):
   - Below neighborhood avg → higher score
   - Above neighborhood avg → lower score
   - Factors in data quality, recency, comparables
5. **Detects anomalies** - Flags listings >50% above/below average
6. **Provides recommendation** - Human-readable assessment

### Web UI

- **Map View:** Leaflet.js with OpenStreetMap tiles
  - Marker clustering for performance
  - Color-coded by price per m² (green=good deal, red=expensive)
  - Click marker for popup with listing preview
- **List View:** Grid of listing cards
  - Filterable by multiple criteria
  - Sortable by price, size, recency
  - Click card to open detail modal
- **Detail Modal:** Full listing info + price analysis
  - Shows deal score, comparables, neighborhood stats
  - Links to original listing

## Customization

### Add a New Scraper

1. Create `scrapers/yoursite_scraper.py`:
```python
from base_scraper import BaseScraper

class YourSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__('yoursite', 'https://yoursite.com')
    
    def scrape(self, city='ciudad-de-mexico', max_pages=3):
        # Your scraping logic
        # Use self.fetch_page(), self.save_html(), etc.
        return self.results
```

2. Add to `run_scrapers.py`:
```python
from yoursite_scraper import YourSiteScraper

scraper4 = YourSiteScraper()
listings4 = scraper4.scrape()
all_listings.extend(listings4)
```

### Adjust Geocoding

Edit `run_scrapers.py` → `DataPipeline.geocode_location()`:
- Change geocoder (Google Maps, Mapbox, etc.)
- Adjust rate limits
- Add fallback geocoders

### Tune Price Intelligence

Edit `price_intelligence.py` → `calculate_deal_score()`:
- Adjust scoring weights
- Change anomaly threshold (currently 50%)
- Add more factors (property age, amenities)

## Limitations & Known Issues

### Prototype Limitations

1. **Scraping Fragility:**
   - Sites change HTML structure → scrapers break
   - Anti-bot measures may block requests
   - Fallback: Sample data generators ensure system works

2. **Geocoding:**
   - OpenStreetMap Nominatim is free but has rate limits (1 req/sec)
   - Some colonias not in OSM database
   - Fallback: Some listings won't have lat/lng

3. **No Historical Data:**
   - Prototype captures single snapshot
   - No price change tracking (yet)
   - Schema supports it, needs repeated scraping

4. **No User Accounts:**
   - Can't save searches or favorites
   - No price alerts
   - Static experience

5. **Single Threaded:**
   - Scrapers run sequentially
   - Slow for large datasets
   - Production needs distributed scraping

### Scraper-Specific Issues

- **Inmuebles24:** May use JavaScript rendering → BeautifulSoup won't see content
  - Fix: Use Playwright/Selenium
- **Vivanuncios:** Cloudflare protection possible
  - Fix: Browser automation with fingerprinting
- **Century21:** Structure varies by country site
  - Fix: Verify you're on .com.mx, not .com

## Production Deployment Checklist

See `ARCHITECTURE.md` for full details. Key items:

- [ ] Migrate to PostgreSQL + PostGIS
- [ ] Set up proxy rotation for scraping
- [ ] Implement browser automation (Playwright) for JS-heavy sites
- [ ] Add more sources (Facebook, broker sites)
- [ ] Integrate INEGI demographic data
- [ ] Add crime/safety data overlay
- [ ] Build user accounts + authentication
- [ ] Implement price alerts (email/push)
- [ ] Create agent dashboard
- [ ] Build mobile apps (React Native)
- [ ] Set up monitoring (Sentry, Datadog)
- [ ] Implement API rate limiting (Redis)
- [ ] Add caching layer (Redis)
- [ ] Deploy on cloud (AWS/GCP)
- [ ] Set up CI/CD pipeline
- [ ] Implement backups and disaster recovery
- [ ] Get legal review (terms, privacy policy)
- [ ] Stress test with 100K+ listings

## Performance

**Current (Prototype):**
- SQLite handles up to ~100K listings adequately
- Map renders 1000s of markers via clustering
- API responses: <100ms for most queries
- Scraping: ~30 listings/minute (with delays)

**Production Targets:**
- PostgreSQL + PostGIS: 10M+ listings
- API responses: <50ms (p95)
- Scraping: 10K+ listings/hour (distributed)
- Map: 100K+ markers with aggregation

## Contributing

This is a prototype. For production development:

1. Follow the architecture in `ARCHITECTURE.md`
2. Write tests (pytest for backend, Jest for frontend)
3. Use type hints (Python 3.10+)
4. Follow PEP 8 style guide
5. Document all public APIs

## License

Prototype for demonstration purposes. Commercial use requires proper licensing for:
- Scraped data (verify source terms of service)
- User-generated content (if adding UGC features)
- Map tiles (OpenStreetMap requires attribution)

## Contact & Support

This is a working prototype demonstrating the concept of a Mexican real estate intelligence platform.

For questions about implementation, see `ARCHITECTURE.md`.

For scaling to production, key priorities are:
1. Robust data acquisition (partnerships > scraping)
2. Price intelligence accuracy (more data, better models)
3. User experience (mobile-first, fast, beautiful)

---

**Built with ❤️ for the Mexican real estate market 🇲🇽**

🐙 **Polpi MX** - Making Mexican real estate data accessible to everyone.
