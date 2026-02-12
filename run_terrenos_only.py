#!/usr/bin/env python3
"""Run MercadoLibre scraper for TERRENOS ONLY with increased page count"""

import sys
import time
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')

# Import and patch the scraper
from mercadolibre_scraper import MercadoLibreScraper
from database import PolpiDB

# Patch the get_search_urls method to only scrape terrenos with 20 pages
original_get_search_urls = MercadoLibreScraper.get_search_urls

def terrenos_only_urls(self, pages_per_category=20):
    """Generate URLs for TERRENOS only"""
    urls = []
    base_path = '/terrenos/venta/distrito-federal/'
    
    for page in range(1, pages_per_category + 1):
        offset = (page - 1) * 50
        if offset == 0:
            url = f"{self.base_url}{base_path}"
        else:
            url = f"{self.base_url}{base_path}_Desde_{offset}"
        
        urls.append({
            'url': url,
            'listing_type': 'sale',
            'property_type': 'terreno',
            'page': page,
            'category': 'sale_terreno'
        })
    
    return urls

# Monkey patch the class
MercadoLibreScraper.get_search_urls = terrenos_only_urls

def main():
    scraper = None
    try:
        # Database stats before
        db = PolpiDB()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        initial_terrenos = cursor.fetchone()['count']
        conn.close()
        
        print("=" * 70)
        print(f"🏞️  TERRENOS-ONLY SCRAPER (MercadoLibre)")
        print(f"   Initial terrenos in DB: {initial_terrenos}")
        print(f"   Target: 200+")
        print(f"   Strategy: 20 pages × 50 listings = 1000 potential terrenos")
        print("=" * 70 + "\n")
        
        # Scrape
        scraper = MercadoLibreScraper()
        print("Starting scrape...")
        listings, stats = scraper.scrape_all(pages_per_category=20, max_listings=300)
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPED {len(listings)} TERRENOS")
        print("=" * 70)
        
        if listings:
            # Show samples
            print(f"\n🏞️  SAMPLE TERRENOS:")
            for i, listing in enumerate(listings[:5], 1):
                price = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                size = listing.get('lot_size_m2') or listing.get('size_m2')
                size_str = f"{size:,.0f} m²" if size else "N/A"
                title = listing.get('title', '')[:70]
                colonia = listing.get('colonia', 'N/A')
                
                print(f"\n   {i}. {title}")
                print(f"      💰 {price}")
                print(f"      📏 {size_str}")
                print(f"      📍 {colonia}")
            
            # Store
            print(f"\n💾 Storing in database...")
            stored = scraper.store_in_database(listings)
            print(f"   ✓ Stored {stored} listings")
        
        # Final stats
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        final_terrenos = cursor.fetchone()['count']
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL RESULT")
        print(f"   Terrenos in DB: {final_terrenos} (+{final_terrenos - initial_terrenos})")
        
        if final_terrenos >= 200:
            print(f"   ✅ GOAL ACHIEVED!")
        else:
            print(f"   📈 Progress: {final_terrenos}/200 ({(final_terrenos/200*100):.1f}%)")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            scraper.close()

if __name__ == '__main__':
    main()
