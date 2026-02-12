# SEDUVI Data Sources Reference
**For Polpi MX Zoning Integration**  
**Last Updated:** February 11, 2026

---

## Primary Data Sources

### 1. SEDUVI SIG Portal (Main Source)

**URLs:**
- Primary: https://sig.cdmx.gob.mx/
- Legacy: http://ciudadmx.cdmx.gob.mx:8080/seduvi/

**What It Provides:**
- Zoning category by address/coordinates
- COS (Coeficiente de Ocupación del Suelo) - Lot coverage
- CUS (Coeficiente de Utilización del Suelo) - Floor Area Ratio
- Allowed uses
- Maximum floors/height
- Over 60 data layers including:
  - Land use (uso de suelo)
  - Mobility infrastructure
  - Public services
  - Environmental data
  - Infrastructure

**Access Methods:**
1. **Web Interface** (Available Now)
   - Manual lookup by entering address or coordinates
   - Visual map display
   - Free public access

2. **API** (To Be Determined)
   - No official API documented
   - May require reverse-engineering portal requests
   - See investigation steps in ZONING_INTEGRATION_PLAN.md

**Search Capabilities:**
- By street address
- By lat/lng coordinates
- By cuenta catastral (cadastral account number)

**Data Format:**
- Web interface: HTML/interactive map
- Potential API: Likely JSON or XML (needs investigation)

**Update Frequency:**
- Updated when new PDDUs are approved
- Typically 1-2 times per year per Alcaldía

---

### 2. Heritage Zone Catalogs (Critical for Development)

**INAH (Instituto Nacional de Antropología e Historia)**
- **URL:** https://catalogonacionalmhi.inah.gob.mx/
- **Covers:** Historic monuments (colonial era, pre-1900)
- **Data:** Catalog of protected buildings
- **Format:** Database/catalog, possibly GeoJSON

**INBA (Instituto Nacional de Bellas Artes)**
- **URL:** http://cartografiasdelpatrimonio.org.mx/
- **Covers:** Artistic monuments (1900-1990, architectural value)
- **Data:** Protected zones and individual buildings
- **Format:** Maps, catalogs

**SEDUVI Heritage Catalog**
- **URL:** Via SIG portal
- **Covers:** City-cataloged heritage structures
- **Data:** Buildings with local protection

**Combined Heritage Map:**
- **URL:** http://cartografiasdelpatrimonio.org.mx/mapas/catalogos/
- **Format:** Interactive map showing all protected zones
- **Usage:** Overlay with property locations to detect heritage restrictions

**Why This Matters:**
- Heritage zones have stricter building codes
- Require INAH/INBA approval (adds 3-6 months)
- Often lower height limits
- Façade modifications restricted
- Critical to flag for investors

---

### 3. Programas Delegacionales (PDDUs)

**What They Are:**
- Detailed urban development programs for each of 16 Alcaldías
- Define zoning for specific neighborhoods
- More detailed than city-wide rules

**Where to Find:**
- **Main Portal:** https://www.seduvi.cdmx.gob.mx/programas-delegacionales-de-desarrollo-urbano
- **Individual Downloads:** PDFs and maps per Alcaldía

**Format:**
- PDF documents (text regulations)
- Static map images (JPG/PNG)
- Some have GIS layers (need to request)

**Alcaldías (Boroughs):**
1. Álvaro Obregón
2. Azcapotzalco
3. Benito Juárez
4. Coyoacán
5. Cuajimalpa
6. Cuauhtémoc
7. Gustavo A. Madero
8. Iztacalco
9. Iztapalapa
10. Magdalena Contreras
11. Miguel Hidalgo
12. Milpa Alta
13. Tláhuac
14. Tlalpan
15. Venustiano Carranza
16. Xochimilco

**Usage:**
- Reference for detailed zoning questions
- Not suitable for automated lookup (PDF format)
- Use as validation source

---

### 4. Normas Generales de Ordenación

**What They Are:**
- City-wide general planning norms
- Standard rules that apply across CDMX
- Define COS, CUS, setbacks, etc.

**Where to Find:**
- **URL:** http://www.data.seduvi.cdmx.gob.mx/portal/index.php/que-hacemos/planeacion-urbana/normas-generales-de-ordenacion
- **Also:** Available through SEDUVI main site

**Format:**
- PDF document
- Legal text

**Key Information:**
- Standard COS/CUS formulas
- Height calculation rules (height ≤ 2× street width)
- Setback requirements
- Open area percentages
- Floor-to-floor heights

**Usage:**
- Reference for calculations
- Understand general rules
- Already incorporated into zoning_lookup.py

---

### 5. Certificado Único de Zonificación (CUS)

**What It Is:**
- Official zoning certificate
- Required for building permits and property transactions
- Legal document with authority

**Where to Get:**
- **Portal:** https://www.seduvi.cdmx.gob.mx/servicios/servicio/certificado_digital
- **In-Person:** SEDUVI offices

**Cost:**
- $2,025 MXN (as of 2025)

**Validity:**
- 1 year from issuance

**Delivery:**
- Digital PDF
- Or physical document (in-person)

**What It Contains:**
- Exact zoning category
- Permitted uses
- Building parameters (COS, CUS, height)
- Special restrictions
- Heritage status

**For Polpi MX:**
- Provide link to request portal
- Suggest users get this for serious deals
- Our zoning lookup is preliminary/informational

---

## Data Access Strategies

### Strategy A: Manual Lookup Integration (Immediate)
**Effort:** Low  
**Cost:** Free  
**Timeline:** 1 day

1. Add "Check Zoning" button to property pages
2. Link to SIG portal with pre-filled coordinates
3. User performs manual lookup

**Pros:** Zero infrastructure, immediate value  
**Cons:** Not automated, requires user effort

---

### Strategy B: Portal Scraping (Recommended for Phase 2)
**Effort:** Medium  
**Cost:** Development time  
**Timeline:** 2-4 weeks

1. Reverse-engineer SIG portal API
2. Build scraper to query by coordinates
3. Parse responses and cache in database
4. Display on Polpi frontend

**Steps to Investigate API:**
```bash
# 1. Open browser DevTools
# 2. Go to https://sig.cdmx.gob.mx/
# 3. Network tab > XHR/Fetch filter
# 4. Enter address/coordinates and search
# 5. Find the request that returns zoning data
# 6. Copy request as cURL or fetch
# 7. Replicate in Python
```

**Example Investigation:**
```python
# After finding the endpoint, test it:
import requests

response = requests.post(
    'https://sig.cdmx.gob.mx/api/query',  # Hypothetical
    json={
        'lat': 19.433,
        'lng': -99.133,
        'layers': ['zonificacion', 'uso_suelo']
    },
    headers={
        'User-Agent': 'Mozilla/5.0...',
        'Referer': 'https://sig.cdmx.gob.mx/'
    }
)

print(response.json())
```

**Pros:** Automated, scalable, good UX  
**Cons:** Requires maintenance, may break if portal changes

---

### Strategy C: Transparency Law Request (Recommended in Parallel)
**Effort:** Low  
**Cost:** Free (legal right)  
**Timeline:** 20-30 days

1. File formal request under Ley General de Transparencia
2. Request bulk GIS data (shapefiles, GeoJSON)
3. Import into Polpi database

**Request Text (Spanish):**
```
Solicitud de Información Pública

Solicitamos acceso a los siguientes datos geoespaciales en formato
digital (shapefile, GeoJSON, o similar):

1. Capa de zonificación completa de la Ciudad de México
2. Polígonos de uso de suelo con atributos de:
   - Categoría de zonificación
   - Coeficiente de Ocupación del Suelo (COS)
   - Coeficiente de Utilización del Suelo (CUS)
   - Número máximo de niveles
   - Usos permitidos

3. Polígonos de zonas de conservación patrimonial

Fundamento: Ley General de Transparencia y Acceso a la Información Pública
```

**Submit To:**
- SEDUVI Unidad de Transparencia
- INFOCDMX platform

**Pros:** Legal right to data, comprehensive dataset  
**Cons:** Takes time, no guarantee of format quality

---

### Strategy D: Official Partnership (Best Long-term)
**Effort:** Medium (negotiation)  
**Cost:** TBD  
**Timeline:** 2-6 months

1. Contact SEDUVI directly
2. Propose official data partnership
3. Request API access or bulk data
4. Potentially pay licensing fee

**Benefits:**
- Official blessing
- API access
- Regular updates
- Marketing opportunity (first partner)

**Who to Contact:**
- SEDUVI Director de Tecnología
- SEDUVI Coordinación de Planeación

**Pitch:**
```
Polpi MX is democratizing access to real estate data for Mexican
developers and investors. Official zoning data integration would help
small developers make informed decisions and increase transparency in
CDMX real estate market. We're willing to prominently attribute SEDUVI
as data source and explore partnership opportunities.
```

---

## Recommended Approach

### Phase 1: Quick Wins (This Week)
- ✅ Prototype complete (zoning_lookup.py)
- ⏭️ Add manual lookup button (Strategy A)
- ⏭️ Download heritage catalogs and create overlay

### Phase 2: Data Acquisition (Weeks 1-4)
- ⏭️ File transparency request (Strategy C)
- ⏭️ Contact SEDUVI for partnership (Strategy D)
- ⏭️ Begin portal investigation (Strategy B)

### Phase 3: Implementation (Weeks 4-8)
- ⏭️ Build scraper if no official data (Strategy B)
- ⏭️ Or integrate bulk data if received (Strategy C/D)
- ⏭️ Enrich database with zoning info
- ⏭️ Launch frontend features

---

## Data Quality Considerations

### Known Issues
1. **Timeliness:** Zoning data may lag actual PDDU updates by months
2. **Accuracy:** Some areas may have overlapping jurisdictions
3. **Completeness:** Rural/peripheral areas may have less detailed data
4. **Format:** PDDUs in PDF make automated extraction difficult

### Validation Strategy
1. **Always link to official sources** - Let users verify
2. **Include update timestamp** - Show when data was last fetched
3. **Disclaimer** - "For informational purposes, verify with official CUS"
4. **Spot-check accuracy** - Manually validate sample of properties
5. **User feedback** - Allow reporting of incorrect data

---

## Technical Stack Recommendations

### For Scraping
- **Python 3.9+**
- **requests** - HTTP client
- **BeautifulSoup4** - HTML parsing
- **Selenium** - If JavaScript rendering required
- **pandas** - Data manipulation

### For GIS Data
- **GDAL/OGR** - Shapefile reading
- **geopandas** - Spatial data analysis
- **Shapely** - Geometric operations
- **PostGIS** (optional) - Spatial database

### For Database
- Current SQLite works fine
- Consider PostgreSQL + PostGIS for advanced spatial queries

### Example: Point-in-Polygon Query
```python
from shapely.geometry import Point, Polygon
import geopandas as gpd

# Load zoning polygons
zoning_gdf = gpd.read_file('cdmx_zoning.geojson')

# Query point
point = Point(-99.133, 19.433)

# Find containing polygon
result = zoning_gdf[zoning_gdf.contains(point)]
print(result['zonificacion'].values[0])  # e.g., "HM4"
```

---

## Next Steps Checklist

- [ ] Add manual lookup button to one property page (test)
- [ ] Draft transparency law request (Spanish)
- [ ] Identify SEDUVI contact for partnership discussion
- [ ] Set up browser automation to investigate SIG portal API
- [ ] Download heritage catalog GeoJSON files
- [ ] Create heritage zone overlay in database
- [ ] Test zoning_lookup.py with 10 real properties
- [ ] Write zoning guide content for users

---

## Contact Information

### SEDUVI
- **Main:** https://metropolis.cdmx.gob.mx/
- **Phone:** 55-5130-2100
- **SIG Support:** Extensions 2313, 2319, 2320, 2299

### INFOCDMX (Transparency Portal)
- **Portal:** https://www.infocdmx.org.mx/
- **File Request:** Online platform

### Academic Resources
- **UNAM Urban Studies** - Potential interns/consultants
- **Colegio de Arquitectos CDMX** - Professional network

---

**Document Purpose:** Quick reference for developers implementing zoning integration  
**Companion Docs:** ZONING_INTEGRATION_PLAN.md, polpi-mx-zoning-research.md  
**Status:** Ready for implementation
