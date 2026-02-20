# Polpi MX - Strategic Roadmap
**Mexican Real Estate Intelligence Platform**  
*"Clean data is the product. Everything else is distribution."*

---

## 🎯 Current State (January 2025)

### What Exists
- **Live Platform**: isaacachar.github.io/polpi-mx
- **Data Coverage**: 83 CDMX listings (proof of concept scale)
- **Data Sources**: 3 active scrapers (Inmuebles24, Vivanuncios, Century21)
- **Database**: SQLite with normalized schema + geocoding
- **Intelligence Layer**: 
  - Deal scoring algorithm
  - Comparables engine
  - Neighborhood statistics
- **Tech Stack**: Static site (data embedded in HTML)
- **UI/UX**: Dark navy + electric blue, modern aesthetic (Airbnb/Zillow hybrid)

### What Works
✅ Scrapers are functional and extracting data  
✅ Data normalization pipeline exists  
✅ Price intelligence algorithms are operational  
✅ UI is polished and deployed  
✅ Basic product-market validation (it looks real)

### Current Limitations
❌ Static build = no real-time updates, no user accounts  
❌ 83 listings = not enough for serious buyers/investors  
❌ CDMX only = limited geographic utility  
❌ No revenue model implemented  
❌ No user feedback loop or analytics  
❌ No competitive moat beyond tech (data is scrapeable by others)

---

## 🚀 Target State - Success Scenarios

### Option A: B2B Data Licensing (Most Viable Short-Term)
**Customer**: Real estate developers, institutional investors, boutique brokerages  
**Product**: Clean, normalized, geocoded MX real estate data + intelligence API  
**Success Looks Like**:
- 5-10 paying B2B customers @ $500-2,000/month each
- MRR: $5,000-15,000 within 12 months
- Coverage: Top 5 Mexican cities (CDMX, Monterrey, Guadalajara, Tijuana, Playa del Carmen)
- 50,000+ active listings in database
- Historical price tracking (3-6 months of data)
- API with 99% uptime, rate limits, authentication

**Why This First**: 
- Fastest path to revenue
- Validates data value before building consumer features
- B2B customers will tell you what data they need
- Lower user acquisition cost than B2C

---

### Option B: B2C Freemium (Medium-Term)
**Customer**: Expat buyers, Mexican investors, remote workers  
**Product**: Free search + premium insights (deal scores, price predictions, neighborhood intel)  
**Success Looks Like**:
- 1,000+ monthly active users
- 100+ paying subscribers @ $20-50/month
- MRR: $2,000-5,000 within 18 months
- User-generated content (reviews, photos, neighborhood tips)
- Mobile app (iOS/Android)

**Why Second**: 
- Requires more features (accounts, payments, mobile)
- Higher CAC, longer sales cycle
- But: builds brand, creates flywheel, enables lead gen

---

### Option C: Lead Generation (Long-Term)
**Customer**: Real estate agents and agencies  
**Product**: Qualified buyer leads  
**Success Looks Like**:
- $50-200 per lead (standard RE market rate)
- 20-50 leads/month = $1,000-10,000/month
- CRM integration for agents
- Lead quality scoring

**Why Last**: 
- Requires significant traffic volume
- Agents are skeptical of new platforms
- Two-sided marketplace problems
- But: Highest potential revenue per user

---

### Option D: Hybrid Model (Ultimate Vision, 24+ months)
- **Data API** for developers/institutions ($500-5k/mo)
- **Premium subscriptions** for power users ($20-50/mo)
- **Lead gen** for agents (performance-based)
- **White-label** for brokerages ($2k-10k/mo)

**Success = $50k+ MRR, self-sustaining team, clear market leadership**

---

## 📍 Phase 1: VALIDATE (Months 1-3)
**Goal**: Prove someone will pay for this. Lock in 1-3 pilot customers.

### Milestones

#### 1.1: Expand Dataset (Priority: HIGH)
**Goal**: Get to 5,000+ CDMX listings minimum to be credible

- [ ] **Scale scrapers**: Add 4-5 more sources (Properati, Lamudi, OLX, Facebook Marketplace)
- [ ] **Run daily scrapes**: Automate cron jobs, error handling
- [ ] **Add historical tracking**: Store price changes over time
- [ ] **Data quality**: De-duplicate, flag anomalies, validate geocodes
- [ ] **Coverage metric**: Track listings per neighborhood (identify gaps)

**Effort**: 2-3 weeks (Joe)  
**Isaac's Role**: Define data quality thresholds, prioritize sources

---

#### 1.2: Build B2B Pitch Deck
**Goal**: 10-slide deck that sells the data value prop

- [ ] Problem: No clean MX RE data (show examples of dirty data)
- [ ] Solution: Polpi's normalized, geocoded, analyzed data
- [ ] Demo: Live platform walkthrough
- [ ] Market size: Developers, investors, brokerages (TAM/SAM/SOM)
- [ ] Pricing: Tiered model (Starter/Pro/Enterprise)
- [ ] Roadmap: What we'll build with their input
- [ ] Team: Why you can execute (technical + domain expertise)
- [ ] Case study: 1-2 example use cases (investment analysis, site selection)

**Effort**: 1 week (Isaac)  
**Joe's Role**: Pull data examples, create visualizations

---

#### 1.3: Identify 20 Target Customers
**Goal**: Build outreach list of companies that need this data

**Target Profiles**:
- Boutique RE developers (10-50 person firms building in CDMX)
- US-based investors buying MX property
- Proptech startups needing MX data
- Large brokerages (RE/MAX, Century21) for their investment arms
- VC firms investing in MX real estate

**Sources**:
- LinkedIn Sales Navigator
- Crunchbase (proptech companies)
- AMPI (Mexican RE association) member list
- Y Combinator companies (MX-focused)

**Effort**: 1 week (Isaac)  
**Joe's Role**: Scrape/organize contact info into CRM

---

#### 1.4: Outreach Campaign
**Goal**: Get 10 discovery calls, convert 1-3 to pilots

**Approach**:
- Cold email (personalized, 3-email sequence)
- LinkedIn DMs
- Warm intros through network (ask friends, advisors)
- Offer: Free 30-day data access in exchange for feedback

**Email Template**:
```
Subject: Clean MX real estate data (finally)

Hi [Name],

I noticed [Company] is [investing in/building in] Mexico City. 

I built Polpi MX (isaacachar.github.io/polpi-mx) — a platform that 
normalizes messy MX real estate data from 8+ sources into a clean, 
geocoded, analyzed database.

No MLS exists here. We're fixing that.

Would you be open to a 15-min demo? Happy to give you free API 
access for 30 days in exchange for feedback.

Best,
Isaac
```

**Effort**: Ongoing, 5-10 hours/week (Isaac)  
**Joe's Role**: Track responses in CRM, schedule calls

---

#### 1.5: Pilot Program (1-3 customers)
**Goal**: Validate willingness to pay, gather feature requests

- [ ] Set up basic API (read-only, JSON endpoints)
- [ ] Create simple auth (API keys)
- [ ] Document endpoints (Postman/Swagger)
- [ ] Weekly check-ins with pilot customers
- [ ] Track usage metrics (which endpoints, query patterns)
- [ ] Ask: "What would you pay for this?"

**Effort**: 2 weeks (Joe builds API, Isaac manages pilots)  
**Pricing**: Free for 30 days, then $500/mo to continue

---

### Phase 1 Success Criteria
✅ 5,000+ CDMX listings in database  
✅ 10+ sales conversations completed  
✅ 1-3 pilot customers using API  
✅ At least 1 verbal commitment to pay  
✅ Clear understanding of what features B2B customers need

**Decision Point**: 
- If YES → Proceed to Phase 2 (build for revenue)
- If NO → Pivot to B2C or shut down

---

## 🏗️ Phase 2: BUILD (Months 4-9)
**Goal**: Turn pilots into paying customers. Scale data and infrastructure.

### Milestones

#### 2.1: Production API (Priority: CRITICAL)
**Goal**: Enterprise-grade API that customers will pay for

**Features**:
- [ ] RESTful API with full CRUD
- [ ] GraphQL endpoint (optional, but modern)
- [ ] Authentication: API keys + OAuth
- [ ] Rate limiting (tier-based: 100, 1000, 10000 requests/day)
- [ ] Webhooks (notify customers of new listings, price changes)
- [ ] Uptime monitoring (99.5%+ SLA)
- [ ] Documentation site (beautiful, interactive)
- [ ] Client libraries (Python, JavaScript)

**Tech Stack Considerations**:
- Move from static site to backend (Node.js/Express or Python/FastAPI)
- PostgreSQL instead of SQLite (handle concurrent connections)
- Redis for caching
- Deploy on Render/Railway/Fly.io (cost-effective, scales)

**Effort**: 4-6 weeks (Joe)  
**Isaac's Role**: Define API specs, test user experience

---

#### 2.2: Geographic Expansion
**Goal**: Cover top 5 Mexican cities for market leadership

**Cities** (in order of priority):
1. **Monterrey**: Wealthy, growing, industrial hub
2. **Guadalajara**: Tech hub, large expat community
3. **Playa del Carmen/Tulum**: Tourist/expat real estate hotspot
4. **Tijuana**: US proximity, cross-border investors
5. **Querétaro**: Fast-growing, manufacturing boom

**Per City**:
- [ ] Identify local listing sites (some sources differ by region)
- [ ] Configure scrapers for new sources
- [ ] Geocode all addresses
- [ ] Validate neighborhood boundaries
- [ ] Add city to API endpoints

**Effort**: 2 weeks per city (Joe)  
**Isaac's Role**: Prioritize cities based on customer demand

**Target**: 50,000+ listings across 5 cities

---

#### 2.3: Enhanced Intelligence Features
**Goal**: Make data more valuable than raw scrapes

**Features to Build**:
- [ ] **Price prediction model**: ML-based (XGBoost/Random Forest)
- [ ] **Market trends**: Price per sqm over time, inventory changes
- [ ] **Investment scoring**: Cap rate estimates, rental yield predictions
- [ ] **Comparable listings**: Better algorithm (location + features + price)
- [ ] **Neighborhood profiles**: Demographics, amenities, crime data
- [ ] **Alert system**: Notify when listings match criteria or drop in price

**Data Sources to Add**:
- INEGI (demographics, census)
- Google Places (amenities)
- OpenStreetMap (infrastructure)
- Historical price archives (web scraping Wayback Machine)

**Effort**: 6-8 weeks (Joe: infrastructure, Isaac: algorithms/validation)

---

#### 2.4: Customer Dashboard (B2B Portal)
**Goal**: Self-service portal for B2B customers

**Features**:
- [ ] Login/account management
- [ ] API key generation and revocation
- [ ] Usage analytics (requests/day, quota remaining)
- [ ] Billing and invoicing (Stripe integration)
- [ ] Support ticket system
- [ ] Saved searches and alerts
- [ ] Export to CSV/Excel

**Effort**: 3-4 weeks (Joe)  
**Isaac's Role**: Design UX, test with customers

---

#### 2.5: Pricing & Packaging
**Goal**: Formalize pricing tiers based on pilot feedback

**Proposed Tiers**:

| Tier | Price | API Calls/Day | Features | Target Customer |
|------|-------|---------------|----------|----------------|
| **Starter** | $500/mo | 1,000 | Basic listings, no historical data | Small brokerages, researchers |
| **Professional** | $1,500/mo | 10,000 | All data + intelligence, 6mo history | Developers, investment firms |
| **Enterprise** | $5,000/mo | 100,000+ | Custom integrations, webhooks, dedicated support | Large institutions |
| **API-only** | $0.01/call | Pay-as-you-go | No minimum, limited features | Startups, experiments |

**Effort**: 1 week (Isaac: pricing strategy, Joe: implement in billing system)

---

#### 2.6: Legal & Compliance
**Goal**: Protect the business and customers

- [ ] Terms of Service (API usage, data restrictions)
- [ ] Privacy Policy (GDPR, LFPDPPP - Mexican data protection law)
- [ ] Scraping legality review (consult lawyer in MX)
- [ ] Entity formation (LLC in US or MX?)
- [ ] Contracts for B2B customers (MSA template)

**Effort**: 2-3 weeks (Isaac: find lawyer, negotiate costs)  
**Budget**: $2,000-5,000 for legal

---

### Phase 2 Success Criteria
✅ 5-10 paying B2B customers  
✅ MRR: $5,000-10,000  
✅ API uptime >99%  
✅ 50,000+ listings across 5 cities  
✅ Historical data for 6+ months  
✅ Churn rate <10%/month

**Decision Point**: 
- If YES → Scale to Phase 3 (growth mode)
- If STUCK → Double down on customer success, iterate product

---

## 💰 Phase 3: MONETIZE & SCALE (Months 10-18)
**Goal**: Achieve $20k+ MRR and explore additional revenue streams

### Milestones

#### 3.1: B2C Freemium Launch
**Goal**: Build consumer brand, acquire users organically

**Free Tier**:
- Search all listings
- Basic filters (price, bedrooms, location)
- View on map
- No deal scores or price predictions

**Premium Tier** ($29/mo or $249/year):
- Deal scores and investment analysis
- Price predictions and trends
- Unlimited saved searches and alerts
- Neighborhood insights
- Export listings to spreadsheet
- Early access to new features

**Features to Build**:
- [ ] User accounts (email/password, Google OAuth)
- [ ] Payment processing (Stripe)
- [ ] Saved searches and favorites
- [ ] Email alerts (daily/weekly digests)
- [ ] Mobile-responsive web app (PWA)
- [ ] Referral program (give 1 month free for referrals)

**Effort**: 8-10 weeks (Joe: full stack, Isaac: product/UX)

---

#### 3.2: Growth & Marketing
**Goal**: Drive traffic to B2C platform

**Channels**:
1. **SEO**: 
   - Blog content (neighborhood guides, market reports)
   - Long-tail keywords ("buy apartment Condesa CDMX")
   - Backlinks from expat forums, MX blogs
   
2. **Content Marketing**:
   - Monthly market reports (free PDFs)
   - "State of MX Real Estate" annual report (PR-worthy)
   - Neighborhood deep-dives (video tours + data)

3. **Communities**:
   - Reddit (r/MexicoCity, r/digitalnomad, r/realestateinvesting)
   - Facebook groups (Expats in CDMX, etc.)
   - Twitter threads (MX RE data stories)

4. **Partnerships**:
   - Relocation services for expats
   - Co-working spaces (WeWork, etc.)
   - Visa consultants (people moving to MX)

5. **Paid Acquisition** (if economics work):
   - Google Ads (high-intent keywords)
   - Facebook/Instagram (target US/Canada users interested in MX)

**Effort**: Ongoing, 10-15 hours/week (Isaac: content, Joe: SEO/analytics)  
**Budget**: $500-2,000/month for ads (test and iterate)

---

#### 3.3: Lead Generation Marketplace
**Goal**: Monetize traffic by connecting buyers with agents

**Model**:
- Buyers fill out "I'm interested" form on listings
- Polpi qualifies leads (budget, timeline, location)
- Sell leads to verified agents for $50-200 each
- Agents pay on delivery or monthly subscription for X leads

**Features**:
- [ ] Lead capture forms on listings
- [ ] Lead qualification quiz
- [ ] Agent onboarding and verification
- [ ] Lead distribution system (rotate among agents)
- [ ] Agent dashboard (see leads, contact info)
- [ ] Payment processing for lead fees

**Challenges**:
- Need enough traffic to generate leads (500+ visitors/day)
- Need to recruit and vet agents
- Need to ensure lead quality (or agents won't pay)

**Effort**: 6-8 weeks (Joe), plus ongoing agent recruitment (Isaac)  
**Target**: 20-50 leads/month @ $100 avg = $2k-5k/month

---

#### 3.4: White-Label / Private Deals
**Goal**: Offer custom solutions to large brokerages

**Product**: 
- White-labeled version of Polpi for brokerages (their brand, our data)
- Private data feeds (custom scrapers for their listings)
- Custom analytics dashboards

**Pricing**: $2,000-10,000/month per client (custom deals)

**Target Customers**:
- RE/MAX Mexico
- Century21 Mexico
- Large local brokerages (KW Mexico, Sotheby's)

**Effort**: Custom dev work per client (scope varies)  
**Isaac's Role**: Sales, negotiation, account management

---

#### 3.5: International Expansion (Optional)
**Goal**: Replicate model in other Latin American markets

**Target Markets** (in order):
1. **Colombia** (Bogotá, Medellín) - expat hotspot, similar data problems
2. **Argentina** (Buenos Aires) - economic opportunity, high demand
3. **Brazil** (São Paulo, Rio) - massive market, but Portuguese = new scrapers

**Considerations**:
- Each country = new scrapers, legal review, localization
- Start with one city per country to test
- Partner with local agents/developers for market knowledge

**Effort**: 3-4 months per country (Joe: tech, Isaac: BD)  
**ROI**: Only pursue if MX is profitable and proven

---

### Phase 3 Success Criteria
✅ MRR: $20,000-50,000  
✅ 5,000+ monthly active users (B2C)  
✅ 50+ paying B2C subscribers  
✅ 10-20 B2B customers  
✅ 20+ leads/month sold to agents  
✅ 1-2 white-label deals  
✅ Team of 2-3 (can hire a junior developer or VA)

**Decision Point**: 
- Continue scaling? Raise funding? Exit?

---

## 👥 Division of Labor

### What Joe Can Do (Technical Execution)
- Build and scale scrapers
- Database design and optimization
- API development and documentation
- Frontend/backend engineering
- DevOps (deployment, monitoring, cron jobs)
- Data analysis and ML models
- Bug fixes and maintenance
- Integration work (Stripe, webhooks, etc.)

**Joe's Superpower**: Turning requirements into working code quickly

---

### What Isaac Must Do (Strategy & Business)
- Customer discovery and sales
- Pricing and packaging decisions
- Pitch deck and marketing materials
- Product prioritization (what to build when)
- Legal and compliance (find lawyers, sign contracts)
- Fundraising (if needed)
- Partnerships and BD
- Content creation (blog, reports, social)
- Hiring (when ready to expand team)

**Isaac's Superpower**: Talking to customers, understanding the market, making decisions

---

### Shared Responsibilities
- **Product design**: Isaac defines requirements, Joe proposes technical approach, iterate together
- **Data quality**: Joe builds pipelines, Isaac spot-checks and defines quality standards
- **Analytics**: Joe instruments tracking, Isaac interprets data and makes decisions
- **Customer support**: Isaac handles sales/strategy questions, Joe handles technical issues

---

## 🛠️ Technical Infrastructure Needs

### Phase 1 (Validation)
- Current setup (SQLite, static site) is fine
- Add cron jobs for daily scrapes
- Simple API (can be read-only Flask app)
- **Cost**: $0-50/month (hosting)

### Phase 2 (Build)
- PostgreSQL database (Supabase or managed Postgres)
- Backend (Node.js or Python)
- Redis for caching
- CDN (Cloudflare)
- Monitoring (Sentry, UptimeRobot)
- **Cost**: $100-300/month

### Phase 3 (Scale)
- Load balancer
- Separate API and web servers
- S3 or equivalent for image storage
- Analytics (Mixpanel or PostHog)
- Email service (SendGrid or Postmark)
- **Cost**: $300-1,000/month

**Key Principle**: Don't over-engineer early. Start simple, scale when needed.

---

## 💵 Financial Projections (Conservative)

### Phase 1 (Months 1-3)
- Revenue: $0-1,500
- Costs: $500 (hosting, legal research, tools)
- **Burn**: -$500

### Phase 2 (Months 4-9)
- Revenue: $5,000-15,000/month (5-10 B2B customers)
- Costs: $2,000/month (hosting, legal, tools, modest salary for Joe)
- **Profit**: $3,000-13,000/month by Month 9

### Phase 3 (Months 10-18)
- Revenue: $20,000-50,000/month (B2B + B2C + lead gen)
- Costs: $8,000/month (infra, salaries for 2-3 people, marketing)
- **Profit**: $12,000-42,000/month by Month 18

**Total Investment Needed**: $10,000-20,000 to get to profitability (or bootstrap with B2B revenue)

---

## 🚨 Risks & Mitigation

### Risk 1: Scrapers break / sites block us
**Likelihood**: HIGH  
**Impact**: CRITICAL (no data = no business)  
**Mitigation**: 
- Rotate IPs/proxies
- Headless browsers + anti-detection
- Diversify sources (8+ sites)
- Build relationships with some brokerages for direct feeds

### Risk 2: No one will pay for the data
**Likelihood**: MEDIUM  
**Impact**: CRITICAL  
**Mitigation**: 
- Validate in Phase 1 before heavy investment
- Pivot to B2C if B2B doesn't work
- Consider freemium model faster

### Risk 3: Legal challenges (scraping)
**Likelihood**: LOW  
**Impact**: HIGH  
**Mitigation**: 
- Consult lawyer in Phase 2
- Terms of Service that protects us
- Precedent: HiQ vs LinkedIn (scraping public data is legal in US)
- Mexico law may differ — research required

### Risk 4: Competition
**Likelihood**: MEDIUM (eventually)  
**Impact**: MEDIUM  
**Mitigation**: 
- Speed: be first to market with clean data
- Relationships: lock in B2B customers with contracts
- Quality: better intelligence layer (not just raw scrapes)
- Geographic coverage: harder to replicate across 5 cities

### Risk 5: Can't scale data fast enough
**Likelihood**: MEDIUM  
**Impact**: MEDIUM  
**Mitigation**: 
- Automate scraping and QA
- Hire junior developer to help Joe
- Outsource data cleaning to VA if needed

---

## 🎯 Key Decisions to Make Soon

1. **B2B-first or B2C-first?**  
   → **Recommendation**: B2B first (faster revenue, validates data value)

2. **What cities to expand to first?**  
   → **Recommendation**: Monterrey, then Guadalajara (based on market size and investor interest)

3. **How much to charge?**  
   → **Recommendation**: Start at $500/mo for Starter tier, adjust based on feedback

4. **When to raise funding?**  
   → **Recommendation**: Bootstrap as long as possible. Only raise if you need to hire a team or expand very fast. Aim for $50k+ MRR before raising.

5. **Should Isaac work on this full-time?**  
   → **Critical decision**: If pilots convert to paying customers in Phase 1, this could justify full-time commitment. Otherwise, keep it as a side project until MRR > personal expenses.

---

## 📊 Success Metrics (KPIs to Track)

### Data Quality
- Number of active listings
- Coverage per city (listings per neighborhood)
- Data freshness (% updated in last 24h)
- De-duplication accuracy

### Customer Acquisition (B2B)
- Sales pipeline (leads → calls → pilots → paying)
- MRR and growth rate
- Customer acquisition cost (CAC)
- Churn rate

### Product Usage
- API calls per day
- Most-used endpoints
- Uptime %
- Support tickets

### B2C (when launched)
- Monthly active users (MAU)
- Conversion rate (free → paid)
- Average revenue per user (ARPU)
- Organic traffic growth

---

## 🚀 Next Actions (This Week)

1. **Isaac**: Review this roadmap, decide on B2B-first approach (Y/N?)
2. **Joe**: Audit current scrapers, estimate effort to add 3-5 more sources
3. **Isaac**: Draft B2B pitch deck (use this roadmap as appendix)
4. **Joe**: Set up daily cron jobs for scraping
5. **Isaac**: Create list of 20 target B2B customers (spreadsheet)
6. **Both**: Schedule 1-hour strategy call to align on Phase 1 priorities

---

## 📚 Appendix: Comparable Companies

- **Redfin** (US): Brokerage + data platform, $1B+ market cap
- **Zillow** (US): Consumer platform, monetizes via ads + lead gen
- **Compass** (US): Agent-focused, tech-enabled brokerage
- **Properati** (LATAM): Listings aggregator (acquired by Navent)
- **Mercado Libre RE** (LATAM): Classifieds, not intelligence-focused
- **HouseCanary** (US): B2B data/valuations, raised $65M
- **Cherre** (US): B2B real estate data, $50M+ raised

**Key Insight**: No one is doing clean, intelligent data for Mexico at scale. The opportunity is real.

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Owner**: Isaac

---

*This is a living document. Update it as you learn, pivot, and grow.*
