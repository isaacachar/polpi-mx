# Polpi MX - Architecture & Growth Strategy

## System Overview

Polpi MX is a real estate aggregation and intelligence platform for the Mexican market, designed to solve the fragmentation problem in Mexican real estate data.

### Current Prototype Architecture

```
┌─────────────────┐
│  Web Scrapers   │ → Inmuebles24, Vivanuncios, Century21
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Pipeline   │ → Normalize, Geocode, Deduplicate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQLite Database │ → Listings, Price History, Stats
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│    Python HTTP API Server           │
│  - Listings API                     │
│  - Price Intelligence Engine        │
│  - Neighborhood Analytics           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Web UI (Vanilla JS)               │
│  - Map View (Leaflet.js)            │
│  - Listing Cards                    │
│  - Price Analysis                   │
└─────────────────────────────────────┘
```

## Production Architecture (Phase 2+)

### Database: PostgreSQL + PostGIS

**Why PostGIS?**
- Spatial queries for "properties within X km"
- Geographic indexing for fast radius searches
- Native support for polygon boundaries (colonias, municipios)
- Much better performance than SQLite for spatial data

**Schema Enhancements:**
```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY,
    source VARCHAR(50),
    source_id VARCHAR(100),
    -- ... fields ...
    location GEOGRAPHY(POINT, 4326),  -- PostGIS type
    colonia_boundary GEOGRAPHY(POLYGON, 4326),
    scraped_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP  -- soft deletes for price history
);

CREATE INDEX idx_location ON listings USING GIST (location);
CREATE INDEX idx_price_city ON listings (city, price_mxn);
CREATE INDEX idx_scraped_at ON listings (scraped_at DESC);
```

### Data Acquisition Strategy

#### Phase 1: Scraping (Current)
- **Pros:** No partnerships needed, fast to launch
- **Cons:** Fragile, blocked easily, incomplete data
- **Sources:**
  - Inmuebles24.com (largest)
  - Vivanuncios.com.mx
  - Century21.com.mx, RE/MAX.com.mx
  - PropiedadesMéxico.com
  - Lamudi.com.mx
  - Facebook Marketplace (harder, requires browser automation)

**Anti-blocking tactics:**
- Residential proxy rotation (Bright Data, Smartproxy)
- Browser fingerprinting (Playwright with realistic profiles)
- Distributed scraping (run from multiple regions)
- Respectful rate limits (1-2 req/sec per site)
- Cache aggressively, scrape incrementally

#### Phase 2: Direct APIs & Partnerships
- Partner with brokerages for exclusive data feeds
- Offer white-label tools in exchange for listings
- MLS integrations (some regions have local MLSs)
- Agent dashboard: "List here for free, get analytics"

#### Phase 3: Public Records Integration
- **Catastro (Property Tax Records):**
  - Each municipality has its own system
  - Some digitized (CDMX, Monterrey, Guadalajara)
  - Contains: property boundaries, tax assessments, owner names (public)
  - Challenges: No unified API, requires custom scrapers per municipality
  
- **Registro Público de la Propiedad (Property Registry):**
  - Public but not digitized in most states
  - Contains: sales history, mortgages, liens
  - Would require partnerships with local governments
  
- **INEGI (National Statistics Institute):**
  - Census data: demographics, income, employment
  - Economic indicators by municipality
  - Free API: https://www.inegi.org.mx/servicios/api_indicadores.html
  - Overlay on neighborhood stats

- **Crime Data:**
  - Federal crime stats from SESNSP
  - Municipality-level data
  - Layer on maps: "safety score"

- **Infrastructure:**
  - Transit data (Metro, Metrobús)
  - Schools, hospitals (Google Places API)
  - Parks, amenities

#### Phase 4: Crowd-Sourced & Agent-Submitted
- Agent portal for direct uploads
- User-submitted "I sold for X" (verify with receipts)
- Price validation through community reporting

### Deduplication at Scale

**Multi-stage approach:**

1. **Exact match:** URL, title, price, address
2. **Fuzzy match:** Levenshtein distance on title/description
3. **Spatial + price:** Same location (within 50m) + price within 5%
4. **Image matching:** Perceptual hashing (pHash) on property photos
5. **ML model:** Train classifier on features:
   - Price similarity
   - Size similarity
   - Location distance
   - Text similarity
   - Image similarity
   - Agent name match

**Output:**
- Canonical listing (best quality source)
- Linked duplicates (hidden from search, used for price validation)

### Price Intelligence Engine

#### Comparable Property Algorithm

**Factors:**
1. **Location weight: 40%**
   - Same colonia: 100%
   - Adjacent colonia: 70%
   - Same city: 40%
   - Distance-based decay

2. **Size weight: 30%**
   - ±10% size: 100%
   - ±20% size: 70%
   - ±30% size: 40%

3. **Property type: 20%**
   - Same type: 100%
   - Similar type (casa vs townhouse): 80%

4. **Recency: 10%**
   - Listed this month: 100%
   - 1-3 months: 90%
   - 3-6 months: 70%
   - Older: 50%

**Implementation:**
```python
SELECT * FROM listings
WHERE city = ?
  AND property_type = ?
  AND ST_DWithin(location, ST_Point(?, ?), 5000)  -- 5km radius
  AND size_m2 BETWEEN ? * 0.8 AND ? * 1.2
  AND scraped_at > NOW() - INTERVAL '6 months'
ORDER BY
  ST_Distance(location, ST_Point(?, ?)) * 0.4 +
  ABS(size_m2 - ?) / ? * 0.3 +
  (EXTRACT(EPOCH FROM NOW() - scraped_at) / 86400) * 0.1
LIMIT 10;
```

#### Price Prediction Model

**Features:**
- Location (lat/lng + colonia embedding)
- Size (m², lot size if casa)
- Bedrooms, bathrooms
- Property type
- Age/condition (if available)
- Amenities (pool, gym, security)
- Proximity to metro, schools, parks
- Neighborhood stats (median income, crime rate)

**Model:** XGBoost Regressor
- Train on listings with stable prices (appeared multiple times)
- Validate on "sold" prices (if we get them)
- Output: predicted price range + confidence interval

#### Trend Detection

**Track:**
- Median price per m² by colonia (weekly)
- Listing velocity (new listings per week)
- Time on market (estimate from scrape frequency)
- Price reductions (when same listing drops price)

**Visualizations:**
- "Hot neighborhoods" (price increasing)
- "Buyer's market" (inventory up, prices flat/down)
- "Days on market" estimates

### API Design

**RESTful API for mobile apps & partners:**

```
GET /api/v1/listings
  ?city=Ciudad+de+México
  &property_type=departamento
  &min_price=2000000
  &max_price=5000000
  &bedrooms=2
  &lat=19.4326
  &lng=-99.1332
  &radius_km=5
  &limit=50
  &offset=0

GET /api/v1/listing/{id}

GET /api/v1/listing/{id}/analysis

GET /api/v1/neighborhoods/{city}
  ?sort=price_per_m2

GET /api/v1/neighborhoods/{city}/{colonia}

GET /api/v1/trends/{city}?period=30d

POST /api/v1/listings
  # For agents to submit listings
  
POST /api/v1/alerts
  # Create price alert for user
```

**Authentication:**
- Free tier: 100 requests/day
- Developer tier: 10,000 requests/day, $49/mo
- Enterprise: Unlimited, custom pricing

**Rate limiting:** Redis-based, by API key

**Webhooks:** Notify partners when new listings match criteria

### Frontend Architecture

**Current:** Vanilla JS (prototype)

**Production:** Next.js + React
- **Why Next.js:**
  - Server-side rendering (SEO critical for real estate)
  - Image optimization (listings are image-heavy)
  - Static generation for neighborhood pages
  - API routes for backend

**Mobile:** React Native
- iOS + Android apps
- Offline-first (cache listings, sync later)
- Push notifications for price alerts

### Infrastructure

**Hosting:**
- **Backend:** AWS/GCP
  - ECS/Cloud Run for API (auto-scaling)
  - PostgreSQL on RDS/Cloud SQL
  - Redis for caching, rate limiting
  - S3/Cloud Storage for images

- **Scraping:** Separate infrastructure
  - Lambda/Cloud Functions for distributed scraping
  - Scraping cluster with rotating proxies
  - Queue-based (SQS/Pub-Sub) for coordination

- **Frontend:** Vercel or Netlify (Next.js optimized)

**Cost estimates (at scale):**
- Database: $200-500/mo (db.m5.large RDS)
- API servers: $100-300/mo (auto-scaling)
- Scraping proxies: $300-1000/mo (depending on volume)
- Storage: $50-100/mo
- CDN: $50-200/mo
- **Total:** ~$700-2100/mo at 100K listings, 50K users

### Monitoring & Observability

**Scraping health:**
- Success rate per source
- Listings scraped per hour
- Blocked IP detection
- Data quality score trends

**API performance:**
- Response time by endpoint
- Error rates
- Rate limit violations

**User analytics:**
- Search patterns (which areas are hot?)
- Conversion funnels (view → save → contact agent)

**Tools:**
- Sentry for error tracking
- Datadog/New Relic for APM
- Google Analytics for user behavior

## Monetization Model

### Free Tier (Consumers)
- Search listings
- View up to 20 details per day
- Basic price comparisons
- Map view

### Premium (Consumers) - $9.99/mo or $99/year
- Unlimited listing views
- Price alerts (email/push when listings match criteria)
- Price drop notifications
- Historical price data
- Neighborhood reports (trends, demographics, crime)
- Save unlimited favorites
- Export listings to CSV

### Pro (Real Estate Agents) - $49/mo
- List unlimited properties for free
- Analytics dashboard (views, engagement)
- Lead capture (buyer inquiries)
- CRM integration (Salesforce, HubSpot)
- Branded listing pages
- Priority placement in search
- API access (100K requests/mo)

### Enterprise (Developers, Institutions) - Custom pricing
- Full API access (unlimited)
- White-label options
- Custom data feeds
- Webhooks for real-time updates
- Historical data exports
- Dedicated support

### Advertising
- Sponsored listings (agents pay for top placement)
- Mortgage/insurance ads targeted by search
- Neighborhood-specific ads (moving companies, furniture)

**Revenue projections (18 months):**
- 10,000 free users
- 500 premium users ($5K/mo)
- 200 agent subscriptions ($10K/mo)
- 10 enterprise clients ($15K/mo)
- Advertising ($5K/mo)
- **Total: $35K/mo = $420K/year**

## Legal Considerations

### Scraping Legality in Mexico
- **Generally legal** if data is publicly accessible
- Respect robots.txt
- Don't violate CFAA equivalent (unauthorized access to systems)
- ToS violations ≠ criminal, but civil liability possible
- Precedent: HiQ Labs v. LinkedIn (US) - public data scraping OK

**Best practices:**
- Scrape politely (rate limits)
- Cache aggressively, scrape incrementally
- Don't scrape logged-in areas
- Provide value-add (not just re-publishing)

### Data Privacy (LFPDPPP - Mexican GDPR)

**Personal data concerns:**
- Agent names, phone numbers (public, OK to republish)
- Property owner names (NOT publicly posted, don't scrape)
- User accounts (our own users):
  - Require consent for email marketing
  - Allow data export/deletion
  - Encrypt passwords (bcrypt)
  - Privacy policy + terms of service

### Intellectual Property
- Listing descriptions: facts = not copyrightable
- Photos: owned by photographer/agent
  - Fair use argument: thumbnails for search
  - Better: link to original or get license
  - Best: host our own (agent uploads)

### Liability
- Disclaimer: "Data aggregated from public sources, verify independently"
- No guarantee of accuracy
- Terms: arbitration clause, liability cap

## Competitive Landscape

### Direct Competitors

**Inmuebles24 (Navent)**
- Largest listing site in MX
- Owned by Mercado Libre (indirect)
- Model: Agents pay to list
- Weakness: No price intelligence, no comparables

**Propiedades.com**
- Second largest
- Similar model to Inmuebles24
- Weakness: Outdated UI, poor mobile experience

**Vivanuncios (Adevinta/eBay)**
- Classifieds model
- Free listings, monetize via ads
- Weakness: Low-quality listings, lots of spam

**Lamudi**
- International player (Emerging Markets Property Group)
- Focus on new developments
- Weakness: Limited coverage in Mexico

### Adjacent Competitors

**Century21, RE/MAX, Coldwell Banker**
- Traditional brokerages with websites
- Only show their own listings
- Weakness: No aggregation across brokers

**Facebook Marketplace**
- Huge volume, especially for rentals
- Weakness: No organization, hard to search

**Google/Mitula/Trovit**
- Listing aggregators (meta-search)
- Weakness: Just links out, no intelligence layer

### U.S. Zillow Analogs (Why they haven't entered MX)

**Zillow, Redfin, Realtor.com**
- Dominance in U.S. due to MLS access
- Mexico has no MLS → much harder to get data
- Cultural/regulatory differences
- Focus on developed markets first

### New Entrants (Proptech Startups)

**Homie (Mexico)**
- Digital brokerage, fixed fee model
- Weakness: Only their own listings

**LaHaus (Colombia → expanding to MX)**
- Digital brokerage + mortgage
- Weakness: Limited to major cities

**Tuhabi (Mexico)**
- Rental focus, property management
- Weakness: Rentals only, not sales

### Our Competitive Advantage

1. **Data aggregation:** We have ALL listings, they have only their own
2. **Price intelligence:** Comparables, deal scores, trends
3. **Neighborhood insights:** Demographics, crime, infrastructure
4. **Free for consumers:** Traditional model charges agents, we monetize differently
5. **Modern UX:** Mobile-first, fast, beautiful
6. **API-first:** Enable ecosystem (other apps, tools)

**Moat:**
- Network effects: More data → better intelligence → more users → more agents → more data
- Switching costs: Users build saved searches, alerts, history
- Data moat: Proprietary historical pricing, cleaned/normalized data

## Growth Strategy

### Phase 1: Launch (Months 0-6)
**Goal:** Prove concept, get to 50K listings, 1K users

**Tactics:**
1. Focus on CDMX (largest market, 30% of MX real estate)
2. Scrape top 5 sources
3. Launch with basic features (search, map, details)
4. SEO: Optimize for "[property type] en [colonia]"
5. Content: Blog posts on "Mejores colonias en CDMX", "Guía de compra"
6. Social: Twitter/IG showing deal alerts, market insights

**Metrics:**
- Listings: 50K
- Users: 1K MAU
- SEO traffic: 5K visits/mo

### Phase 2: Expand Coverage (Months 6-12)
**Goal:** National coverage, 500K listings, 10K users

**Tactics:**
1. Add Monterrey, Guadalajara, Puebla, Querétaro
2. More sources: Facebook, broker sites
3. Implement price intelligence engine
4. Launch mobile apps
5. Premium tier ($9.99/mo)
6. PR: "La app que está revolucionando el mercado inmobiliario"

**Metrics:**
- Listings: 500K
- Users: 10K MAU, 100 paid
- Revenue: $1K/mo

### Phase 3: Monetize (Months 12-18)
**Goal:** $20K MRR, profitability

**Tactics:**
1. Agent tier ($49/mo) - CRM, analytics, lead gen
2. API/developer tier
3. Integrate INEGI data for neighborhood reports
4. Historical price tracking
5. Partnerships with mortgage/insurance companies (affiliate revenue)
6. Sponsored listings

**Metrics:**
- Revenue: $20K/mo
- Users: 50K MAU, 500 paid, 100 agents
- Cost: $5K/mo (servers, proxies)
- **Profit: $15K/mo**

### Phase 4: Dominate (Months 18-36)
**Goal:** Become THE platform, $100K MRR

**Tactics:**
1. Acquire smaller competitors (Lamudi?)
2. Partner with banks for mortgage pre-approval
3. "iBuyer" model: Polpi buys, renovates, resells (high risk, high reward)
4. Agent tools: virtual tours, AI staging
5. International: Expand to LatAm (Colombia, Argentina)

**Metrics:**
- Revenue: $100K/mo
- Users: 200K MAU
- Market share: 20% of online real estate searches in Mexico

### Exit Strategy

**Potential acquirers:**
1. **Mercado Libre** (owns Inmuebles24) - consolidation play
2. **Softbank** (invested in OLX, Loft in Brazil) - LatAm proptech thesis
3. **Zillow/Redfin** - international expansion
4. **PropTech funds** (Fifth Wall, MetaProp)

**Valuation comps:**
- Zillow: 1.5x revenue at IPO
- Rightmove (UK): 10x revenue (mature, profitable)
- REA Group (Australia): 15x revenue

**Conservative:** 3-5x revenue = $3.6-6M at $100K MRR
**Optimistic:** 8-10x revenue = $9.6-12M at $100K MRR

**Timeline:** 3-5 years to exit

## Technical Roadmap

**Q1 2024:**
- ✅ Prototype (current)
- Production PostgreSQL + PostGIS migration
- Add 3 more scraping sources
- Improve deduplication (image hashing)

**Q2 2024:**
- Mobile apps (React Native)
- Premium tier launch
- Historical price tracking
- API v1 public release

**Q3 2024:**
- INEGI integration (neighborhood demographics)
- Agent dashboard
- CRM integrations (Salesforce, HubSpot)
- Price prediction model (XGBoost)

**Q4 2024:**
- Monterrey, Guadalajara expansion
- Crime data overlay
- Transit/infrastructure layer
- White-label API for partners

**2025:**
- Full national coverage
- Mobile-first redesign
- AR property views
- AI-powered search ("3 bed casa near good schools under $5M")

---

## Conclusion

Polpi MX has the opportunity to become the Zillow of Mexico by solving the data fragmentation problem. The market is huge (2nd largest in LatAm), the competition is weak (no dominant player), and the technology barriers are surmountable.

**Key success factors:**
1. Data quality and coverage
2. Price intelligence (the "secret sauce")
3. User experience (mobile-first, fast, beautiful)
4. Network effects (more data → more users → more agents)

**Risks:**
1. Scraping blocks (mitigation: diversify sources, partnerships)
2. Competition from incumbents (mitigation: move fast, differentiate)
3. Regulatory (mitigation: legal counsel, data privacy compliance)

**The opportunity:** Build the infrastructure layer for Mexican real estate. Every property transaction, every price check, every market report flows through Polpi.

**Let's build it. 🐙**
