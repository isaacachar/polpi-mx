# 🚀 Polpi MX - Quick Start Guide

## System is READY TO USE! ✅

The Polpi MX prototype is fully functional with **57 sample listings** across 8 major Mexican cities.

## 1. Access the Web Interface

**Open in your browser:** http://localhost:8000

The server is currently running and ready to use!

## What You Can Do Right Now

### 🗺️ Map View
- See all properties plotted on an interactive map
- Markers color-coded by price per m²:
  - 🟢 Green = Good deal (< 30K MXN/m²)
  - 🟠 Orange = Average (30-50K MXN/m²)
  - 🔴 Red = Expensive (> 50K MXN/m²)
- Click markers for property details popup
- Zoom and pan to explore different areas

### 📋 List View
- Browse properties in a clean grid layout
- Each card shows:
  - Price (MXN and USD)
  - Location (colonia, city)
  - Bedrooms, bathrooms, size
  - Source (inmuebles24, vivanuncios, century21)
  - Price per m²
- Click any card to see full analysis

### 🔍 Filters
Use the sidebar to filter by:
- **City** (8 cities available)
- **Property Type** (casa, departamento, terreno, oficina)
- **Price Range** (MXN)
- **Bedrooms** (minimum)
- **Bathrooms** (minimum)
- **Size** (m² range)

### 💰 Price Intelligence
Click any property to see:
- **Deal Score** (0-100) - Higher = better value
- **Price per m²** compared to neighborhood average
- **Comparable properties** nearby
- **Neighborhood statistics**
- **Recommendation** (good deal, overpriced, market rate)

## 2. Sample Queries via API

The API is also running at http://localhost:8000/api

### Get all listings
```bash
curl http://localhost:8000/api/listings
```

### Get listings in Ciudad de México
```bash
curl "http://localhost:8000/api/listings?city=Ciudad%20de%20México"
```

### Get departamentos under $5M
```bash
curl "http://localhost:8000/api/listings?property_type=departamento&max_price=5000000"
```

### Get database stats
```bash
curl http://localhost:8000/api/stats
```

### Get price analysis for a listing
```bash
curl http://localhost:8000/api/analyze/{listing_id}
```
(Replace {listing_id} with an actual ID from the listings)

## 3. Current Data

### Cities Covered (57 listings total)
- **Ciudad de México** - 10 colonias (Polanco, Roma Norte, Condesa, Santa Fe, etc.)
- **Monterrey** - 4 colonias (San Pedro, Valle Oriente, Centro)
- **Guadalajara** - 4 colonias (Providencia, Puerta de Hierro)
- **Zapopan** - 2 colonias
- **Querétaro** - 2 colonias (Juriquilla, Centro Histórico)
- **Puebla** - 2 colonias (Angelópolis, Centro Histórico)
- **Naucalpan** - 1 colonia (Satellite)
- **Huixquilucan** - 1 colonia (Interlomas)

### Property Types
- Departamentos: ~35%
- Casas: ~35%
- Terrenos: ~20%
- Otros: ~10%

### Price Range
- Low: ~$1.5M MXN
- High: ~$20M MXN
- Average: ~$5-6M MXN

### Sources
- Inmuebles24: 14 listings
- Vivanuncios: 27 listings
- Century21: 16 listings

## 4. Re-populate Database

To regenerate sample data:

```bash
cd ~/Desktop/polpi-mx
source venv/bin/activate
python populate_sample_data.py
```

## 5. Restart Server

If you need to restart:

```bash
# Stop current server (Ctrl+C in terminal, or find process)
ps aux | grep api_server
kill <pid>

# Start again
cd ~/Desktop/polpi-mx
source venv/bin/activate
python api_server.py
```

Server will be available at: http://localhost:8000

## 6. Run Real Scrapers (Experimental)

**Warning:** May be blocked by anti-bot protections. Sample data is more reliable for the prototype.

```bash
cd ~/Desktop/polpi-mx
source venv/bin/activate

# Quick mode (1 page per source)
python run_scrapers.py --quick

# Full mode (2 pages per source)
python run_scrapers.py
```

This will:
- Attempt to scrape real listings from Mexican sites
- Fall back to sample data if blocked
- Add results to the database
- Show statistics when complete

## 7. Database Location

SQLite database: `~/Desktop/polpi-mx/data/polpi.db`

To inspect:
```bash
sqlite3 ~/Desktop/polpi-mx/data/polpi.db

# Inside sqlite3:
.tables
SELECT COUNT(*) FROM listings;
SELECT city, COUNT(*) FROM listings GROUP BY city;
.quit
```

## 8. Next Steps for Development

See `ARCHITECTURE.md` for full production roadmap, but key priorities:

1. **More data sources** - Add Facebook Marketplace, more broker sites
2. **Better scraping** - Use Playwright for JavaScript-rendered sites
3. **PostgreSQL migration** - For production scale and spatial queries
4. **User accounts** - Save searches, price alerts
5. **Mobile apps** - React Native for iOS/Android
6. **INEGI integration** - Add demographic data to neighborhoods
7. **Crime data overlay** - Safety scores by area

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
python api_server.py 8080
```

### No listings showing
```bash
# Re-populate database
python populate_sample_data.py
```

### Map not loading
- Check browser console for errors
- Ensure internet connection (Leaflet.js loads from CDN)
- Try hard refresh (Cmd+Shift+R on Mac)

### CSS not loading
- Check that files exist: `web/css/style.css`, `web/js/app.js`
- Check browser console for 404 errors
- Clear browser cache

## Demo Flow

1. **Open http://localhost:8000**
2. **Map View** - See properties scattered across Mexico
3. **Click a marker** - View property snapshot
4. **Switch to List View** - Browse all properties
5. **Use filters** - Try "Ciudad de México" + "departamento" + price range
6. **Click a listing card** - See full price analysis
7. **Check Deal Score** - Is this a good deal?
8. **View comparables** - What are similar properties priced at?
9. **Explore neighborhoods** - Which colonias are most expensive?

---

## 🎉 You're Ready!

The system is fully functional. Explore the data, test the features, and check out `ARCHITECTURE.md` for the vision of what this becomes at scale.

**Built with ❤️ for the Mexican real estate market 🇲🇽**
