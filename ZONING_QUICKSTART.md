# Zoning Integration - Quick Start Guide
**For Developers Implementing SEDUVI Zoning Features**

---

## 🚀 Get Started in 5 Minutes

### 1. Test the Prototype

```bash
cd /Users/isaachomefolder/Desktop/polpi-mx
source venv/bin/activate

# Run the demo
python3 zoning_lookup.py

# You should see zoning examples for:
# - Centro Histórico (Heritage Area)
# - Polanco (High-density Mixed Use)
# - Buildable area calculations
```

---

### 2. Update Your Database

```bash
# Add zoning columns (safe to run multiple times)
python3 integrate_zoning_example.py add-columns

# Check current status
python3 integrate_zoning_example.py stats

# Enrich a few listings to test
python3 integrate_zoning_example.py enrich 10
```

**Expected output:**
```
✅ Successfully enriched: 10 listings
```

---

### 3. View Enriched Data

```bash
# Check stats again
python3 integrate_zoning_example.py stats

# You should now see zoning data populated
```

---

## 📋 Immediate Implementation (30 minutes)

### Add Manual Lookup Button to Property Pages

**In your property template** (e.g., `web/property_detail.html`):

```html
<!-- Add this to the property details section -->
<div class="zoning-section">
  <h3>🏙️ Zoning Information</h3>
  
  {% if property.lat and property.lng %}
    <a href="https://sig.cdmx.gob.mx/?lat={{ property.lat }}&lng={{ property.lng }}" 
       target="_blank" 
       class="btn btn-outline-secondary">
      Check Zoning on SEDUVI Portal
    </a>
    <p class="text-muted small">
      View official zoning category, building parameters, and allowed uses
    </p>
  {% else %}
    <p class="text-muted">Zoning lookup requires property coordinates</p>
  {% endif %}
</div>
```

**That's it!** You now have basic zoning lookup integrated.

---

## 🎯 Show Cached Zoning Data (If Available)

**In your property template:**

```html
{% if property.zoning_category %}
<div class="zoning-info-card">
  <h4>Zoning: {{ property.zoning_category }}</h4>
  <p>{{ property.zoning_category_full }}</p>
  
  <div class="zoning-details">
    <div class="row">
      <div class="col-md-4">
        <strong>Max Floors:</strong><br>
        {{ property.zoning_max_floors or 'N/A' }}
      </div>
      <div class="col-md-4">
        <strong>Lot Coverage:</strong><br>
        {{ (property.zoning_max_cos * 100)|round(1) if property.zoning_max_cos else 'N/A' }}%
      </div>
      <div class="col-md-4">
        <strong>Floor Area Ratio:</strong><br>
        {{ property.zoning_max_cus|round(2) if property.zoning_max_cus else 'N/A' }}
      </div>
    </div>
  </div>
  
  {% if property.is_heritage_zone %}
  <div class="alert alert-warning">
    ⚠️ <strong>Heritage Zone:</strong> This property may be in a protected historic district. 
    Construction may require INAH or INBA approval (adds 3-6 months to permits).
  </div>
  {% endif %}
  
  <div class="zoning-actions">
    <a href="https://www.seduvi.cdmx.gob.mx/servicios/servicio/certificado_digital" 
       target="_blank" 
       class="btn btn-sm btn-primary">
      📜 Request Official Certificate ($2,025 MXN)
    </a>
  </div>
  
  <p class="text-muted small">
    Last updated: {{ property.zoning_updated_date|date }}
  </p>
</div>
{% endif %}
```

---

## 🔧 API Endpoints

### Add to `api_server.py`:

```python
from zoning_lookup import SEDUVIZoningLookup

@app.get("/api/v1/listings/{listing_id}/zoning")
def get_listing_zoning(listing_id: str):
    """Get zoning information for a specific listing"""
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM listings WHERE id = ?', (listing_id,))
    listing = cursor.fetchone()
    conn.close()
    
    if not listing:
        return {"error": "Listing not found"}, 404
    
    # If no cached zoning data, look it up
    if not listing['zoning_category'] and listing['lat'] and listing['lng']:
        lookup = SEDUVIZoningLookup(use_mock_data=True)  # Change to False when scraper is ready
        zoning = lookup.lookup_by_coordinates(listing['lat'], listing['lng'])
        
        if zoning:
            # Cache it in database
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE listings SET
                    zoning_category = ?,
                    zoning_max_floors = ?,
                    zoning_max_cos = ?,
                    zoning_max_cus = ?
                WHERE id = ?
            ''', (zoning.category, zoning.max_floors, zoning.max_cos, zoning.max_cus, listing_id))
            conn.commit()
            conn.close()
    
    return {
        "listing_id": listing_id,
        "zoning": {
            "category": listing['zoning_category'],
            "category_full": listing['zoning_category_full'],
            "max_floors": listing['zoning_max_floors'],
            "max_cos": listing['zoning_max_cos'],
            "max_cus": listing['zoning_max_cus'],
            "is_heritage_zone": listing['is_heritage_zone'],
        }
    }

@app.post("/api/v1/zoning/lookup")
def zoning_lookup(request):
    """Direct zoning lookup by coordinates"""
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    
    if not lat or not lng:
        return {"error": "lat and lng required"}, 400
    
    lookup = SEDUVIZoningLookup(use_mock_data=True)
    zoning = lookup.lookup_by_coordinates(lat, lng)
    
    if not zoning:
        return {"error": "Zoning not found"}, 404
    
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

## 📊 Buildable Area Calculator

### Add JavaScript Calculator to Property Page:

```html
<div class="buildable-calculator">
  <h4>📐 Buildable Area Calculator</h4>
  
  <div class="form-group">
    <label>Lot Size (m²):</label>
    <input type="number" id="lotSize" value="{{ property.lot_size_m2 or 500 }}" class="form-control">
  </div>
  
  <button onclick="calculateBuildable()" class="btn btn-primary">Calculate</button>
  
  <div id="buildableResults" style="display:none; margin-top:1rem;">
    <h5>Development Potential:</h5>
    <table class="table">
      <tr>
        <td>Maximum Footprint:</td>
        <td><strong id="maxFootprint">-</strong> m²</td>
      </tr>
      <tr>
        <td>Maximum Total Construction:</td>
        <td><strong id="maxConstruction">-</strong> m²</td>
      </tr>
      <tr>
        <td>Maximum Floors:</td>
        <td><strong id="maxFloors">-</strong></td>
      </tr>
      <tr>
        <td>Required Open Area:</td>
        <td><strong id="openArea">-</strong> m²</td>
      </tr>
    </table>
  </div>
</div>

<script>
function calculateBuildable() {
  const lotSize = parseFloat(document.getElementById('lotSize').value);
  const cos = {{ property.zoning_max_cos or 0.7 }};
  const cus = {{ property.zoning_max_cus or 2.8 }};
  const floors = {{ property.zoning_max_floors or 4 }};
  const minOpen = {{ property.zoning_min_open_area_pct or 30 }};
  
  const maxFootprint = lotSize * cos;
  const maxConstruction = lotSize * cus;
  const openArea = lotSize * (minOpen / 100);
  
  document.getElementById('maxFootprint').textContent = maxFootprint.toFixed(2);
  document.getElementById('maxConstruction').textContent = maxConstruction.toFixed(2);
  document.getElementById('maxFloors').textContent = floors;
  document.getElementById('openArea').textContent = openArea.toFixed(2);
  document.getElementById('buildableResults').style.display = 'block';
}
</script>
```

---

## 🔄 Background Enrichment

### Run Nightly to Enrich All Listings

Create `scripts/enrich_zoning_nightly.sh`:

```bash
#!/bin/bash
cd /Users/isaachomefolder/Desktop/polpi-mx
source venv/bin/activate

# Enrich up to 100 listings per night (rate limiting)
python3 integrate_zoning_example.py enrich 100

# Log results
echo "$(date): Zoning enrichment completed" >> logs/zoning_enrichment.log
```

Add to crontab:
```bash
# Run at 2 AM daily
0 2 * * * /Users/isaachomefolder/Desktop/polpi-mx/scripts/enrich_zoning_nightly.sh
```

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `zoning_lookup.py` | Core zoning lookup tool |
| `integrate_zoning_example.py` | Database integration & enrichment |
| `ZONING_INTEGRATION_PLAN.md` | Complete implementation roadmap |
| `SEDUVI_DATA_SOURCES.md` | Data sources & access strategies |
| `ZONING_PROJECT_SUMMARY.md` | Project overview & accomplishments |

---

## 🐛 Troubleshooting

### "No such column: zoning_category"
```bash
# Add the columns first
python3 integrate_zoning_example.py add-columns
```

### "ModuleNotFoundError: No module named 'requests'"
```bash
# Make sure you're in the venv
source venv/bin/activate
pip install -r requirements.txt
```

### "No listings have coordinates"
```bash
# Check your listings
python3 integrate_zoning_example.py stats

# If needed, run geocoding first
python3 geocode_listings.py
```

### Zoning data seems wrong
Currently using **mock data** for testing. To use real data:
1. Build SEDUVI portal scraper (see ZONING_INTEGRATION_PLAN.md)
2. Change `use_mock_data=False` in code
3. Or wait for SEDUVI data partnership

---

## ✅ Checklist for Launch

- [ ] Database columns added (`add-columns`)
- [ ] Manual lookup button added to property pages
- [ ] At least 50 listings enriched with zoning data
- [ ] Zoning display tested on staging site
- [ ] API endpoints implemented and tested
- [ ] Disclaimer added: "For informational purposes, verify with official CUS"
- [ ] Link to SEDUVI certificate portal added
- [ ] Analytics tracking added for zoning feature usage

---

## 🔜 Next Steps

### Phase 2: Automation
1. Reverse-engineer SEDUVI SIG portal
2. Build production scraper
3. Replace mock data with real lookups
4. See `ZONING_INTEGRATION_PLAN.md` for details

### Phase 3: Advanced Features
1. Heritage zone overlay
2. Buildable area calculator
3. Zoning search filters
4. Development potential scoring

---

## 📞 Need Help?

**Documentation:**
- Main plan: `ZONING_INTEGRATION_PLAN.md`
- Data sources: `SEDUVI_DATA_SOURCES.md`
- Project summary: `ZONING_PROJECT_SUMMARY.md`

**Code Examples:**
- Look at `zoning_lookup.py` demo function
- Check `integrate_zoning_example.py` for database patterns

**SEDUVI Resources:**
- Portal: https://sig.cdmx.gob.mx/
- Support: 55-5130-2100 ext. 2313, 2319, 2320, 2299

---

**Last Updated:** February 11, 2026  
**Status:** Ready for immediate implementation  
**Estimated Time to First Deploy:** 30 minutes (manual lookup button)
