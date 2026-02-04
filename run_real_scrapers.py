#!/usr/bin/env python3
"""
Real data scraper for CDMX - gets actual listings from live websites
Focuses on getting real data, not generating samples
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from real_estate_scraper import CDMXRealEstateScraper
from database import PolpiDB
from price_intelligence import PriceIntelligence
import json
from datetime import datetime
import time

class RealDataPipeline:
    def __init__(self):
        self.db = PolpiDB()
        self.price_intel = PriceIntelligence()
        
    def process_listing(self, raw_listing: dict) -> dict:
        """Process and clean raw listing data"""
        listing = raw_listing.copy()
        
        # Ensure required fields have defaults
        if not listing.get('state'):
            listing['state'] = 'Ciudad de México'
        if not listing.get('city'):
            listing['city'] = 'Ciudad de México'
            
        # Clean up price data
        if listing.get('price_mxn'):
            try:
                listing['price_mxn'] = float(listing['price_mxn'])
                if not listing.get('price_usd'):
                    listing['price_usd'] = round(listing['price_mxn'] / 17.0, 2)
            except:
                listing['price_mxn'] = None
                listing['price_usd'] = None
        
        # Clean up numeric fields
        for field in ['bedrooms', 'bathrooms', 'parking_spaces']:
            if listing.get(field):
                try:
                    listing[field] = int(listing[field])
                except:
                    listing[field] = None
        
        for field in ['size_m2', 'lot_size_m2', 'lat', 'lng']:
            if listing.get(field):
                try:
                    listing[field] = float(listing[field])
                except:
                    listing[field] = None
        
        # Ensure lists are properly formatted
        if listing.get('images') and isinstance(listing['images'], str):
            listing['images'] = [listing['images']]
        
        return listing
    
    def save_to_database(self, listings: list) -> int:
        """Save all listings to database"""
        print(f"\n💾 Saving {len(listings)} listings to database...")
        
        success_count = 0
        error_count = 0
        
        for i, raw_listing in enumerate(listings):
            try:
                # Process listing
                processed = self.process_listing(raw_listing)
                
                # Skip listings without essential data
                if not processed.get('title') or not processed.get('price_mxn'):
                    error_count += 1
                    continue
                
                # Insert into database
                listing_id = self.db.insert_listing(processed)
                success_count += 1
                
                if (i + 1) % 25 == 0:
                    print(f"  Processed {i + 1}/{len(listings)} listings...")
            
            except Exception as e:
                print(f"  Error processing listing {i+1}: {e}")
                error_count += 1
        
        print(f"✅ Successfully saved {success_count} listings")
        if error_count > 0:
            print(f"❌ {error_count} listings failed to save")
        
        return success_count
    
    def calculate_market_intelligence(self):
        """Run price intelligence calculations on real data"""
        print("\n🧮 Calculating market intelligence...")
        
        try:
            # Get all colonias with listings
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT colonia, COUNT(*) as listing_count 
                FROM listings 
                WHERE colonia IS NOT NULL AND city = 'Ciudad de México'
                GROUP BY colonia
                ORDER BY listing_count DESC
            """)
            
            colonias = cursor.fetchall()
            conn.close()
            
            print(f"  Found {len(colonias)} CDMX colonias with listings")
            
            # Calculate stats for each colonia
            for colonia_row in colonias:
                colonia = colonia_row['colonia']
                count = colonia_row['listing_count']
                
                # Get neighborhood stats
                stats = self.db.get_neighborhood_stats('Ciudad de México', colonia)
                if stats:
                    print(f"  {colonia}: {count} listings, avg ${stats['avg_price_mxn']:,.0f} MXN")
            
            print("✅ Market intelligence calculated")
            
        except Exception as e:
            print(f"❌ Error calculating market intelligence: {e}")
    
    def print_results_summary(self):
        """Print comprehensive results summary"""
        stats = self.db.get_stats()
        
        print("\n" + "=" * 70)
        print("🎉 REAL CDMX DATA SCRAPING COMPLETE")
        print("=" * 70)
        print(f"📊 Total listings: {stats['total_listings']}")
        print(f"🏙️  Cities: {stats['cities']}")
        print(f"🏘️  Neighborhoods: {stats['colonias']}")
        
        print(f"\n📊 Listings by source:")
        for source, count in stats['sources'].items():
            print(f"   • {source}: {count} listings")
        
        # Show sample listings
        sample_listings = self.db.get_listings(filters={'city': 'Ciudad de México'}, limit=3)
        if sample_listings:
            print(f"\n🏠 Sample listings:")
            for listing in sample_listings:
                print(f"   • {listing['title']}")
                print(f"     ${listing['price_mxn']:,.0f} MXN in {listing['colonia']}")
                print(f"     {listing['size_m2']:.0f}m² | Quality: {listing['data_quality_score']}")
                print()
        
        # Show neighborhood breakdown
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT colonia, COUNT(*) as count, 
                   AVG(price_mxn) as avg_price,
                   AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
            FROM listings 
            WHERE colonia IS NOT NULL AND city = 'Ciudad de México'
            GROUP BY colonia 
            ORDER BY avg_price_per_m2 DESC
            LIMIT 10
        """)
        
        top_colonias = cursor.fetchall()
        conn.close()
        
        if top_colonias:
            print(f"🏆 Top CDMX neighborhoods by price/m²:")
            for row in top_colonias:
                colonia = row['colonia']
                count = row['count']
                avg_price_per_m2 = row['avg_price_per_m2'] or 0
                print(f"   • {colonia}: {count} listings, ${avg_price_per_m2:,.0f} MXN/m²")
        
        print(f"\n✅ Database ready at: data/polpi.db")
        print(f"🚀 Start web interface: python3 api_server.py")

def main():
    """Main execution function"""
    print("🏠 POLPI MX - REAL CDMX DATA SCRAPER")
    print("=" * 70)
    print("🎯 Target: Real CDMX property listings from live websites")
    print("🚫 NOT generating fake data - scraping actual properties")
    print("=" * 70)
    
    pipeline = RealDataPipeline()
    
    # Initialize scraper
    scraper = CDMXRealEstateScraper()
    
    # Scrape real listings
    print("\n🚀 Starting real data collection...")
    all_listings = scraper.scrape_all()
    
    if not all_listings:
        print("❌ No listings collected! Check network connection and site availability.")
        return
    
    # Save to database
    success_count = pipeline.save_to_database(all_listings)
    
    if success_count == 0:
        print("❌ No listings saved to database!")
        return
    
    # Calculate market intelligence
    pipeline.calculate_market_intelligence()
    
    # Print final summary
    pipeline.print_results_summary()
    
    # Save scraping summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_scraped': len(all_listings),
        'total_saved': success_count,
        'target_colonias': [
            'Polanco', 'Condesa', 'Roma Norte', 'Roma Sur', 'Santa Fe',
            'Coyoacán', 'Del Valle', 'Narvarte', 'San Ángel', 
            'Lomas de Chapultepec', 'Pedregal', 'Juárez', 'Cuauhtémoc',
            'Nápoles', 'Interlomas'
        ],
        'data_source': 'real_estate_scraping'
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/real_scrape_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nScraping summary saved to: data/real_scrape_summary.json")

if __name__ == '__main__':
    main()