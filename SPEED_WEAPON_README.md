# ⚡ Polpi MX Speed Weapon - Phase 1 MVP

## What Was Built

A single-page web application that analyzes Mexican real estate listings instantly. Paste a URL from Lamudi, MercadoLibre, or Inmuebles24 and get comprehensive market intelligence in under 30 seconds.

## 🚀 Quick Start

### 1. Start the Server

```bash
cd ~/Desktop/polpi-mx
source venv/bin/activate
python3 api_server.py
```

### 2. Open the Tool

Navigate to: **http://localhost:8000/analyze.html**

### 3. Analyze a Listing

Paste any of these URLs:
- Lamudi: `https://www.lamudi.com.mx/detalle/...`
- MercadoLibre: `https://inmuebles.mercadolibre.com.mx/...`
- Inmuebles24: `https://www.inmuebles24.com/...`

Click **"Analyze"** and get instant results.

## 📊 What You Get

### 1. Property Basics
- Title, price, size (m²), lot size
- Bedrooms, bathrooms, property type
- Location (colonia, city)
- Source platform

### 2. Zoning & Development Potential
*(when coordinates are available)*
- SEDUVI zoning category (e.g., HM4, H3)
- Max allowed floors
- Buildable area calculations:
  - Max footprint (ground floor)
  - Max total construction (all floors)
  - **Price per buildable m²** - Key developer metric!
- Required open area
- Allowed uses
- Heritage zone warnings

### 3. Market Analysis
- Price vs market average (%)
- Market position (Below/Above/At market)
- Listing price per m²
- Neighborhood average price per m²
- Data quality score

### 4. Comparable Listings
- Up to 5 similar properties from your database
- Same colonia and property type
- Quick comparison table with prices and specs

## 🛠️ Technical Implementation

### New Files Created

1. **`url_analyzer.py`** - Core scraping module
   - Extracts property data from individual listing URLs
   - Supports Lamudi, MercadoLibre, Inmuebles24
   - Handles different HTML structures for each site
   - Extracts coordinates from embedded maps

2. **`web/analyze.html`** - Frontend UI
   - Clean, Notion-style design
   - Responsive layout (mobile-friendly)
   - Real-time loading states
   - Inline results display (no page refresh)

3. **API Endpoint** - Added to `api_server.py`
   - `POST /api/v1/analyze-url`
   - Request: `{"url": "https://..."}`
   - Response: Property data + zoning + comps + analysis

### Integration Points

- **`zoning_lookup.py`** - Used for SEDUVI zoning data
  - `lookup_by_coordinates()` - Get zoning by lat/lng
  - `calculate_buildable_area()` - Max construction calculations

- **`database.py`** - PolpiDB for comparables
  - Queries listings by colonia + property type
  - Returns top 5 matches for comparison

- **Existing API Server** - FastAPI at port 8000
  - New endpoint integrated seamlessly
  - Uses existing CORS, logging, error handling

## 🎨 Design Philosophy

**Notion-Inspired Aesthetic:**
- Clean, minimal interface
- Professional typography (system fonts)
- Generous whitespace
- Data-dense but not cluttered
- Dark navy (#1a3a52) + clean whites
- No stock photos, no fluff

**User Flow:**
1. Single input field (URL)
2. One button (Analyze)
3. Inline results (no navigation)
4. Instant feedback (loading states)

## 📝 Code Quality

- **Modular:** Each component has clear responsibility
- **Error Handling:** Graceful degradation (missing data doesn't break UI)
- **Type Hints:** Python code uses dataclasses and type annotations
- **Logging:** All API calls logged for debugging
- **Responsive:** Works on mobile and desktop

## 🧪 Testing

### Manual Test Checklist

1. ✅ Server starts without errors
2. ✅ Frontend loads at `/analyze.html`
3. ✅ API endpoint responds to POST requests
4. ✅ URL analyzer extracts data from test URLs
5. ✅ Zoning lookup integrates correctly
6. ✅ Comparables query works
7. ✅ Results display properly in UI

### Quick API Test

```bash
curl -X POST http://localhost:8000/api/v1/analyze-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.lamudi.com.mx/detalle/..."}'
```

## 🔧 Configuration

**Environment:**
- Python virtual environment: `venv/`
- Dependencies: FastAPI, BeautifulSoup, cloudscraper, requests
- Database: SQLite (`data/polpi.db`)
- Port: 8000

**Static Files:**
- Location: `web/` directory
- Served by FastAPI StaticFiles
- analyze.html accessible at `/analyze.html`

## 📈 Future Enhancements (Phase 2+)

1. **Better Geocoding:**
   - Integrate Google Maps API for address → coordinates
   - More accurate location data

2. **Real SEDUVI Integration:**
   - Scrape actual SEDUVI portal (currently uses mock data)
   - Get official zoning certificates

3. **Enhanced Scraping:**
   - Handle more edge cases
   - Extract additional fields (amenities, parking, etc.)
   - Support more listing sites

4. **Analytics:**
   - Save analyzed URLs to database
   - Track which listings get analyzed most
   - Build dataset for ML price predictions

5. **Export Features:**
   - PDF report generation
   - CSV export for comps
   - Email sharing

## 🐛 Known Limitations

1. **Zoning Data:** Currently uses mock data based on coordinates
   - Real SEDUVI integration needed for production
   - Heritage zone detection is approximate

2. **Geocoding:** Not all listings have coordinates
   - Missing coords = no zoning/buildable data
   - Need address → lat/lng service

3. **Scraping Reliability:**
   - Sites change HTML structure over time
   - Cloudflare protection on some sites
   - Rate limiting considerations

4. **Comps Matching:**
   - Basic colonia + type matching
   - Could be smarter (size range, price range)

## 💡 Usage Tips

**For Developers:**
- Input any terreno (land) listing to see buildable m² calculations
- Price per buildable m² is key metric for development deals
- Compare to comps to spot underpriced opportunities

**For Investors:**
- Market position indicator shows if listing is a deal
- Comparables give quick neighborhood context
- Zoning info critical for change-of-use potential

**For Analysts:**
- Use this to quickly screen 10-20 listings
- Export results (future) for further analysis
- Build proprietary dataset from searches

## 🎯 Success Criteria

✅ **Speed:** Analysis completes in under 30 seconds
✅ **Design:** Clean, professional, Notion-like aesthetic
✅ **Utility:** Provides actionable data (buildable m², market position)
✅ **Integration:** Uses existing codebase (zoning_lookup, database)
✅ **Local-Only:** Works on localhost, no GitHub push needed

## 📞 Support

**Error: "Unsupported URL source"**
- Check URL is from Lamudi, MercadoLibre, or Inmuebles24
- Make sure URL is complete (includes https://)

**Error: "Failed to extract property data"**
- Site may have changed HTML structure
- Check internet connection
- Try a different listing

**No Zoning Data:**
- Listing doesn't have coordinates in source HTML
- Currently normal for some sites
- Future: Add geocoding service

**No Comparables:**
- Database doesn't have listings in that colonia
- Try a different neighborhood
- Run scrapers to populate more data

---

## 🎉 Summary

You now have a working "Speed Weapon" tool that:
1. Takes any Mexican listing URL
2. Scrapes property data
3. Looks up zoning and calculates buildable area
4. Finds comparable listings
5. Shows market positioning
6. Displays everything in a clean, professional interface

**Time to first analysis:** < 30 seconds ⚡

Built with ❤️ for Polpi MX
