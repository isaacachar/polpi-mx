# Location Analyzer - Speed Weapon v2.0

## 🎯 The Pivot: No More Scraping!

Instead of scraping listing URLs (which get blocked), the new Location Analyzer accepts:
- **Addresses** (e.g., "Polanco", "Av. Presidente Masaryk, Polanco")
- **Colonia names** (e.g., "Roma Norte", "Condesa")
- **Coordinates** (e.g., "19.433, -99.133")

We then provide development intelligence from public data sources.

## 🚀 Quick Start

1. **Start the server** (if not already running):
   ```bash
   cd ~/Desktop/polpi-mx
   source venv/bin/activate
   python api_server.py
   ```

2. **Open in browser**:
   ```
   http://localhost:8000/location-analyze.html
   ```

3. **Enter a location**:
   - Type: `Polanco` (colonia name)
   - Or: `19.433, -99.133` (coordinates)
   - Or: `Av. Presidente Masaryk, Polanco` (full address)

4. **Optional: Add lot size**:
   - Enter lot size in m² (e.g., `500`)
   - Get buildable area calculations
   - See development potential (apartments, hotel rooms, offices)

5. **Click "Analyze Location"**

## 📊 What You Get

### 1. Location Confirmation
- Exact coordinates
- Colonia name
- Delegación (borough)
- Full formatted address

### 2. Zoning Information
- Zoning category (e.g., HM4 = Mixed Residential, 4 floors)
- Max floors allowed
- Lot coverage (COS) - how much of lot can be covered
- Floor Area Ratio (FAR/CUS) - total buildable area
- Allowed uses (residential, commercial, hotel, etc.)
- Heritage zone warnings

### 3. Buildable Area (if lot size provided)
- Max footprint (ground floor)
- Max total construction area
- Required open space

### 4. Development Potential
Automatic calculations for:
- **Apartments**: Units @ 60m² and 80m² each
- **Hotel rooms**: Rooms @ 35m² each
- **Office space**: Usable m² (85% efficiency)

### 5. Market Context
From our database (573 listings):
- Average price per m² in the colonia
- Min/max price per m²
- Total active listings
- **Price per buildable m²** (land cost / buildable area)

### 6. Comparables
Recent listings in the same colonia from our database

## 🔧 Technical Details

### API Endpoint
```
POST /api/v1/analyze-location
```

**Request:**
```json
{
  "location": "Roma Norte",
  "lot_size_m2": 500  // optional
}
```

**Response:**
```json
{
  "location": { ... },
  "zoning": { ... },
  "buildable": { ... },
  "development_potential": { ... },
  "market_data": { ... },
  "comparables": [ ... ]
}
```

### Data Sources

1. **Geocoding**: Nominatim (OpenStreetMap)
   - Free, no API key required
   - Rate limit: 1 request/second
   - Handles CDMX addresses well

2. **Zoning**: `zoning_lookup.py`
   - Currently uses mock data based on typical CDMX zoning
   - Returns realistic zoning info based on coordinates
   - Can be upgraded to real SEDUVI data

3. **Market Data**: Our database
   - 573 scraped listings
   - Colonia-level price averages
   - Property type filters

### Key Calculations

**Buildable Area:**
```
max_footprint = lot_size × COS
max_construction = lot_size × CUS
required_open_area = lot_size × (min_open_area_pct / 100)
```

**Development Units:**
```
apartments_60m2 = max_construction / 60
apartments_80m2 = max_construction / 80
hotel_rooms = max_construction / 35
office_usable = max_construction × 0.85
```

**Price per Buildable m²:**
```
price_per_buildable = (avg_price_per_m2 × lot_size) / max_construction
```

## 🎨 UI/UX Features

- **Notion-style design**: Clean, minimal, professional
- **Instant results**: No page reload
- **Smart input parsing**: Auto-detects address vs coordinates
- **Progressive disclosure**: Only shows sections with data
- **Responsive**: Works on mobile and desktop

## 📝 Example Use Cases

### 1. Quick Colonia Check
**Input:** `Polanco`  
**Use:** "What's the zoning in Polanco? What can I build there?"

### 2. Development Feasibility
**Input:** `Roma Norte` + `500` m²  
**Use:** "I found a 500m² lot in Roma Norte. How many apartments can I build? What's the land cost per buildable m²?"

### 3. Coordinate Lookup
**Input:** `19.433, -99.133`  
**Use:** "I have GPS coordinates from a map. What's the zoning here?"

### 4. Full Analysis
**Input:** `Av. Presidente Masaryk 261, Polanco` + `1000` m²  
**Use:** "Complete development analysis for a specific address"

## 🔮 Future Enhancements

### Phase 2: Real SEDUVI Data
- Integrate actual SEDUVI portal API
- Real-time zoning lookups
- Heritage zone verification (INAH/INBA catalogs)
- Permit history by area

### Phase 3: Enhanced Market Data
- Price trends over time
- Recent permits in area
- Development activity heatmaps
- ROI calculations

### Phase 4: Permitting Intelligence
- Required permits by use type
- Estimated timeline
- Cost estimates
- Contact info for tramites

## 🐛 Known Limitations

1. **Mock Zoning Data**: Currently uses heuristic zoning based on coordinates. Real SEDUVI integration coming soon.

2. **Limited Market Data**: Only shows data for colonias in our database (currently ~30 colonias with scraped data).

3. **Geocoding Rate Limits**: Nominatim has 1 req/sec limit. If doing bulk analysis, add delays.

4. **No Property Ownership Data**: Can't verify if lot is available for sale.

## 💡 Tips

- **Use colonia names** for quickest results (fastest to geocode)
- **Add lot size** to get the full development potential analysis
- **Check heritage zones** - they have stricter regulations and longer permit times
- **Compare multiple colonias** by running multiple searches

## 🆚 Location Analyzer vs URL Analyzer

| Feature | Location Analyzer | URL Analyzer |
|---------|------------------|--------------|
| Input | Address/Coordinates/Colonia | Listing URL |
| Scraping | No (uses public data) | Yes (extracts from listing) |
| Blocking Risk | None | High |
| Zoning Data | ✅ Full zoning info | ✅ If coordinates available |
| Development Potential | ✅ With lot size input | ✅ If lot size in listing |
| Market Comps | ✅ From database | ✅ From database |
| Use Case | Planning/Research | Listing evaluation |

**Recommendation:** 
- Use **Location Analyzer** for development research and planning
- Use **URL Analyzer** for evaluating specific listings you found online

## 🎯 Success Metrics

The tool is working well if you can:
1. ✅ Enter any CDMX colonia and get zoning info
2. ✅ See realistic buildable area calculations
3. ✅ Get market price context when available
4. ✅ Understand what you could build on a lot

## 📞 Support

Questions? Check:
- API docs: `http://localhost:8000/docs`
- Main README: `README.md`
- Zoning docs: `ZONING_QUICKSTART.md`

---

Built with ❤️ for CDMX real estate developers and investors.
