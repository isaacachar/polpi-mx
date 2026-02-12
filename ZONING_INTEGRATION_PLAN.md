# SEDUVI Zoning Integration Plan for Polpi MX
**Date:** February 11, 2026  
**Status:** Phase 1 Complete (Prototype Ready)

---

## Executive Summary

✅ **Prototype Completed:** `zoning_lookup.py` provides working zoning lookup framework  
🎯 **Goal:** Add zoning data to Polpi MX listings so developers know what they can build  
📊 **Impact:** Unique differentiator in Mexican real estate market (no competitors offer this)

---

## Phase 1: Prototype & Research (COMPLETE)

### Deliverables ✅

1. **`zoning_lookup.py`** - Working prototype with:
   - Zoning category lookup by coordinates
   - Buildable area calculations (COS/CUS formulas)
   - Heritage zone detection
   - Mock data system for testing
   - Framework ready for real SEDUVI portal integration

2. **Comprehensive Research** - See `/Users/isaachomefolder/clawd/memory/polpi-mx-zoning-research.md`
   - CDMX zoning system documentation
   - SEDUVI data source analysis
   - Technical feasibility assessment
   - Comparison with US systems

### Key Findings

**Good News:**
- CDMX zoning is **simpler than US** - centralized system with ~10 main categories
- Polpi already has lat/lng coordinates in database (ready for integration)
- Free government GIS portal exists (https://sig.cdmx.gob.mx/)
- No competitors in Mexico offer this feature

**Challenges:**
- No official API - requires custom scraping
- No third-party data providers (unlike US: Regrid, Zoneomics)
- Portal may require reverse-engineering
- Heritage zones need separate data integration

---

## Phase 2: Quick Wins (NEXT STEPS)

**Timeline:** 1-2 weeks  
**Effort:** Low  
**Value:** Medium-High

### 1. Manual Lookup Integration (Immediate)

Add "Check Zoning" button to property detail pages that:
- Links directly to SEDUVI SIG portal with pre-filled coordinates
- Opens in new tab: `https://sig.cdmx.gob.mx/?lat={lat}&lng={lng}`
- User performs manual lookup (low-tech but functional)

**Implementation:**
```python
# In property detail page template
def get_seduvi_lookup_url(listing):
    if listing.lat and listing.lng:
        return f"https://sig.cdmx.gob.mx/?lat={listing.lat}&lng={listing.lng}"
    return None
```

**Value:** Immediate utility with zero infrastructure cost

### 2. Educational Content

Create zoning guide section:
- "Understanding CDMX Zoning" article
- Glossary (H, HM, HO, COS, CUS, etc.)
- "What Can I Build?" calculator (client-side)
- Video walkthrough of SEDUVI portal

**Value:** Positions Polpi as authoritative resource

### 3. Heritage District Overlay

Flag properties in known heritage zones:
- Download INAH/INBA catalogs from http://cartografiasdelpatrimonio.org.mx/
- Create simple polygon overlay in database
- Show warning: "⚠️ Property may be in protected heritage zone"

**Value:** Critical info for developers, prevents costly mistakes

---

## Phase 3: Basic Automation (RECOMMENDED)

**Timeline:** 4-6 weeks  
**Effort:** Medium  
**Value:** High

### 1. SEDUVI Portal Scraper

**Approach:**
1. Reverse-engineer SIG portal network requests
2. Build scraper to query by coordinates
3. Parse HTML/JSON responses
4. Extract: zoning category, COS, CUS, allowed uses, max floors
5. Cache results in database

**Technical Steps:**
```bash
# 1. Inspect portal requests (using browser DevTools)
# Look for XHR/Fetch requests when entering coordinates

# 2. Replicate requests in Python
import requests

session = requests.Session()
response = session.post(
    'https://sig.cdmx.gob.mx/api/zoning-query',  # Hypothetical endpoint
    json={'lat': 19.433, 'lng': -99.133}
)

# 3. Parse response
zoning_data = response.json()
```

**Database Schema Addition:**
```sql
ALTER TABLE listings ADD COLUMN zoning_category TEXT;
ALTER TABLE listings ADD COLUMN zoning_max_floors INTEGER;
ALTER TABLE listings ADD COLUMN zoning_max_cos REAL;
ALTER TABLE listings ADD COLUMN zoning_max_cus REAL;
ALTER TABLE listings ADD COLUMN zoning_allowed_uses TEXT;
ALTER TABLE listings ADD COLUMN zoning_updated_date TEXT;
ALTER TABLE listings ADD COLUMN is_heritage_zone BOOLEAN DEFAULT 0;
```

### 2. Automated Zoning Enrichment

Create background job to enrich existing listings:
```python
# enrich_zoning_data.py
from database import PolpiDB
from zoning_lookup import SEDUVIZoningLookup

db = PolpiDB()
lookup = SEDUVIZoningLookup(use_mock_data=False)

# Get listings without zoning data
listings = db.get_listings_without_zoning()

for listing in listings:
    if listing.lat and listing.lng:
        zoning = lookup.lookup_by_coordinates(listing.lat, listing.lng)
        if zoning:
            db.update_listing_zoning(listing.id, zoning)
            print(f"✅ Updated {listing.id}: {zoning.category}")
```

### 3. Frontend Display

Add zoning card to property detail pages:
```html
<div class="zoning-info-card">
  <h3>🏙️ Zoning Information</h3>
  
  <div class="zoning-category">
    <strong>{{ listing.zoning_category }}</strong>
    <span class="badge">{{ zoning_category_name }}</span>
  </div>
  
  <div class="zoning-details">
    <div class="detail-item">
      <label>Max Floors:</label>
      <span>{{ listing.zoning_max_floors }}</span>
    </div>
    <div class="detail-item">
      <label>Lot Coverage (COS):</label>
      <span>{{ listing.zoning_max_cos * 100 }}%</span>
    </div>
    <div class="detail-item">
      <label>Floor Area Ratio (CUS):</label>
      <span>{{ listing.zoning_max_cus }}</span>
    </div>
  </div>
  
  <div class="buildable-calculator">
    <button onclick="showBuildableCalculator()">
      📐 Calculate Buildable Area
    </button>
  </div>
  
  <div class="official-cert">
    <a href="{{ get_seduvi_cert_url() }}" target="_blank">
      📜 Request Official CUS Certificate ($2,025 MXN)
    </a>
  </div>
</div>
```

---

## Phase 4: Advanced Features

**Timeline:** 3-6 months  
**Effort:** High  
**Value:** Very High

### 1. Interactive Buildable Area Calculator

Input parameters:
- Lot size (from listing)
- Zoning category (from database)
- Optional: Current construction size

Output:
- Maximum buildable area
- Number of floors allowed
- Estimated number of units (residential)
- Development potential score (%)

**Example:**
```
🏗️ Development Potential Analysis

Current lot: 600m²
Current building: 450m² (2 floors)
Zoning: HM4 (Mixed Residential, 4 floors)

Maximum Buildable:
  • Footprint: 420m² (70% COS)
  • Total construction: 1,680m² (CUS 2.8)
  • Floors allowed: 4
  
Current vs. Potential:
  • Current: 450m² (27% of max)
  • Unused potential: 1,230m² (73%)
  
💡 Opportunity: This property is significantly under-built!
   Potential to add ~1,200m² of construction.
```

### 2. Zoning Search Filters

Add filters to property search:
- "Show only under-built properties" (development upside)
- "Mixed-use zoning" (HM, HC, HCS)
- "6+ floors allowed" (high-density opportunities)
- "Not in heritage zone" (faster permitting)

### 3. Proprietary Zoning Database

Build comprehensive CDMX zoning database:
- Systematically query all SEDUVI data
- Include all 16 Alcaldías PDDUs
- Track zoning changes over time
- Provide as API to partners

**Competitive Moat:** First mover in Mexico zoning data

---

## Technical Implementation Guide

### Data Sources to Integrate

1. **SEDUVI SIG Portal** (Primary)
   - URL: https://sig.cdmx.gob.mx/
   - Method: Scrape or reverse-engineer API
   - Data: Zoning category, COS, CUS, allowed uses

2. **Heritage Catalogs** (Critical)
   - INAH: https://catalogonacionalmhi.inah.gob.mx/
   - INBA: http://cartografiasdelpatrimonio.org.mx/
   - Method: Download GeoJSON/shapefiles
   - Data: Protected zone boundaries

3. **Programas Delegacionales** (Reference)
   - URL: https://www.seduvi.cdmx.gob.mx/programas-delegacionales
   - Method: Manual download (PDFs)
   - Data: Detailed zoning maps per Alcaldía

### Scraper Architecture

```python
# zoning_scraper.py
import requests
from bs4 import BeautifulSoup
import json

class SEDUVIScraper:
    """
    Scraper for SEDUVI SIG portal.
    Reverse-engineered from browser network requests.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://sig.cdmx.gob.mx"
        
    def get_zoning_by_coordinates(self, lat, lng):
        """
        Query SEDUVI portal for zoning info.
        
        NOTE: This is a placeholder. Actual implementation requires
        inspecting the portal's network requests to find the real endpoint.
        """
        # Step 1: Identify the API endpoint
        # - Open https://sig.cdmx.gob.mx/ in browser
        # - Open DevTools > Network tab
        # - Enter coordinates and submit
        # - Find the XHR/Fetch request that returns zoning data
        
        # Step 2: Replicate the request
        # Example (hypothetical):
        response = self.session.post(
            f"{self.base_url}/api/query",
            json={
                'lat': lat,
                'lng': lng,
                'layers': ['zoning', 'land_use']
            }
        )
        
        # Step 3: Parse response
        if response.ok:
            data = response.json()
            return self._parse_zoning_response(data)
        
        return None
    
    def _parse_zoning_response(self, data):
        """
        Extract zoning info from portal response.
        """
        # Extract relevant fields based on actual response structure
        return {
            'category': data.get('zonificacion'),
            'cos': data.get('cos'),
            'cus': data.get('cus'),
            # ... etc
        }
```

### Database Integration

Update `database.py` to include zoning operations:

```python
# Add to PolpiDB class
def update_listing_zoning(self, listing_id: str, zoning: ZoningInfo):
    """Update listing with zoning information"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE listings SET
            zoning_category = ?,
            zoning_max_floors = ?,
            zoning_max_cos = ?,
            zoning_max_cus = ?,
            zoning_allowed_uses = ?,
            is_heritage_zone = ?,
            zoning_updated_date = ?
        WHERE id = ?
    ''', (
        zoning.category,
        zoning.max_floors,
        zoning.max_cos,
        zoning.max_cus,
        json.dumps(zoning.allowed_uses),
        zoning.is_heritage_zone,
        datetime.now().isoformat(),
        listing_id
    ))
    
    conn.commit()
    conn.close()

def get_listings_without_zoning(self):
    """Get all listings that need zoning enrichment"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM listings
        WHERE lat IS NOT NULL 
          AND lng IS NOT NULL
          AND zoning_category IS NULL
        LIMIT 100
    ''')
    
    listings = cursor.fetchall()
    conn.close()
    return listings
```

### API Endpoints

Add zoning endpoints to `api_server.py`:

```python
@app.get("/api/v1/listings/{listing_id}/zoning")
def get_listing_zoning(listing_id: str):
    """Get zoning information for a specific listing"""
    db = PolpiDB()
    listing = db.get_listing(listing_id)
    
    if not listing:
        return {"error": "Listing not found"}, 404
    
    if not listing.zoning_category:
        # Trigger on-demand lookup if not cached
        lookup = SEDUVIZoningLookup()
        zoning = lookup.lookup_by_coordinates(listing.lat, listing.lng)
        if zoning:
            db.update_listing_zoning(listing_id, zoning)
    
    return {
        "listing_id": listing_id,
        "zoning": {
            "category": listing.zoning_category,
            "max_floors": listing.zoning_max_floors,
            "max_cos": listing.zoning_max_cos,
            "max_cus": listing.zoning_max_cus,
            "allowed_uses": json.loads(listing.zoning_allowed_uses),
            "is_heritage_zone": listing.is_heritage_zone,
        },
        "buildable": calculate_buildable_area(listing)
    }

@app.post("/api/v1/zoning/lookup")
def zoning_lookup(lat: float, lng: float):
    """Direct zoning lookup by coordinates"""
    lookup = SEDUVIZoningLookup()
    zoning = lookup.lookup_by_coordinates(lat, lng)
    
    if not zoning:
        return {"error": "Zoning not found for coordinates"}, 404
    
    return {
        "category": zoning.category,
        "category_full": zoning.category_full,
        "max_floors": zoning.max_floors,
        "max_cos": zoning.max_cos,
        "max_cus": zoning.max_cus,
        "allowed_uses": zoning.allowed_uses,
        "is_heritage_zone": zoning.is_heritage_zone,
    }
```

---

## Legal & Compliance Considerations

### 1. Data Usage Rights

**Options:**
1. **Transparency Law Request** - File formal request under Ley General de Transparencia
   - Request bulk GIS data from SEDUVI
   - Legal right to public data
   - May take 20-30 days

2. **Scraping** - Reverse-engineer portal
   - Review terms of service first
   - Add proper attribution to SEDUVI
   - Include disclaimer: "For informational purposes only"

3. **Partnership** - Contact SEDUVI directly
   - Propose official data partnership
   - May establish precedent for future proptech companies

**Recommendation:** Attempt #3 first (partnership), then #1 (transparency request), fallback to #2 (scraping)

### 2. Disclaimers

Always include:
```
⚠️ DISCLAIMER
This zoning information is provided for informational purposes only.
Always verify with official Certificado Único de Zonificación (CUS)
from SEDUVI before making investment decisions. Zoning regulations
may change, and heritage restrictions may apply.
```

### 3. Data Freshness

- Update zoning data quarterly (SEDUVI updates periodically)
- Show last updated date on all zoning displays
- Flag listings with zoning data >6 months old

---

## Cost Estimates

### Phase 2 (Quick Wins)
- Manual lookup integration: **1 day dev** ($500)
- Educational content creation: **$2,000-3,000** (writer + designer)
- Heritage overlay: **1 week dev** ($3,000)
- **Total: ~$5,500-6,500**

### Phase 3 (Basic Automation)
- Portal reverse-engineering: **1-2 weeks** ($5,000-10,000)
- Scraper development: **2 weeks** ($10,000)
- Database integration: **1 week** ($5,000)
- Frontend implementation: **2 weeks** ($10,000)
- **Total: ~$30,000-35,000**

### Phase 4 (Advanced Features)
- Buildable calculator: **2-3 weeks** ($15,000)
- Search filters: **1 week** ($5,000)
- Proprietary database: **Ongoing** ($20,000-40,000)
- **Total: ~$40,000-60,000**

**Alternative:** Partner with Mexican GIS firm to co-develop (could reduce costs 30-40%)

---

## Success Metrics

### Immediate (Phase 2)
- [ ] Manual lookup button on all listings with coordinates
- [ ] Zoning guide published
- [ ] Heritage zones flagged for 1,000+ listings

### Short-term (Phase 3)
- [ ] 80%+ of listings have zoning data cached
- [ ] Zoning info displayed on property detail pages
- [ ] 20%+ of users engage with zoning features
- [ ] 5+ leads mention zoning as key decision factor

### Long-term (Phase 4)
- [ ] Comprehensive CDMX zoning database complete
- [ ] Buildable area calculator used on 30%+ of listings
- [ ] Zoning filters used in 10%+ of searches
- [ ] Polpi MX recognized as authoritative zoning resource

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SEDUVI portal changes | Medium | High | Flexible scraper architecture, monitor for changes, maintain fallback to manual lookup |
| Legal issues with scraping | Low | Medium | Pursue transparency request, include proper disclaimers, consult legal counsel |
| Data accuracy problems | Medium | High | Always link to official sources, include "verify with CUS" disclaimer, regular audits |
| Development cost overruns | Medium | Medium | Start with MVP (Phase 2), validate demand before Phase 3/4 investment |
| Low user engagement | Low | Medium | Conduct user testing, gather feedback, iterate on UX |

---

## Next Steps (Recommended)

### Immediate (This Week)
1. ✅ Prototype complete (`zoning_lookup.py`)
2. ⏭️ Add manual lookup button to one property page (test)
3. ⏭️ Contact SEDUVI to inquire about data partnership

### Next 2 Weeks
4. ⏭️ File transparency law data request
5. ⏭️ Begin heritage zone data integration
6. ⏭️ Create zoning guide content

### Next Month
7. ⏭️ Reverse-engineer SEDUVI portal (if no official partnership)
8. ⏭️ Build production scraper
9. ⏭️ Begin database enrichment

### Next Quarter
10. ⏭️ Launch zoning features publicly
11. ⏭️ Gather user feedback
12. ⏭️ Plan Phase 4 advanced features

---

## Competitive Advantage

**Why This Matters:**

1. **No Competition:** Zero Mexican real estate platforms offer zoning analysis
2. **High Value:** Critical info for developers/investors (can make or break deals)
3. **Sticky Feature:** Once users rely on it, hard to switch platforms
4. **Data Moat:** Building proprietary database creates barrier to entry
5. **US Parity:** Brings Polpi MX to feature parity with sophisticated US platforms

**Market Positioning:**
> "Polpi MX: The only platform that shows you what you can build, not just what exists."

---

## Appendix: Quick Reference

### CDMX Zoning Categories
- **H** = Residential (Habitacional)
- **HC** = Residential + Ground-floor Commercial
- **HM** = Mixed Residential (Most common in valuable areas)
- **HO** = Residential + Offices
- **E** = Public Facilities (Equipamiento)
- **I** = Industrial
- **AV** = Green Areas (Áreas Verdes)

### Key Metrics
- **COS** (Coeficiente de Ocupación del Suelo) = Lot coverage (%)
- **CUS** (Coeficiente de Utilización del Suelo) = Floor Area Ratio
- **Density suffix** = Number (e.g., HM4 = 4 floors allowed)

### Important Links
- SEDUVI SIG Portal: https://sig.cdmx.gob.mx/
- Heritage Catalog: http://cartografiasdelpatrimonio.org.mx/
- Official Certificate: https://www.seduvi.cdmx.gob.mx/servicios/servicio/certificado_digital

---

**Document Status:** Ready for implementation  
**Next Review:** After Phase 2 completion  
**Owner:** Polpi MX Development Team
