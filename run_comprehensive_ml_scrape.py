#!/usr/bin/env python3
"""Comprehensive MercadoLibre scrape - all categories"""

import sys
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from mercadolibre_improved_scraper import MercadoLibreImprovedScraper
from database import PolpiDB

def main():
    scraper = MercadoLibreImprovedScraper()
    
    # Get initial stats
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM listings')
    initial_total = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
    initial_ml = cursor.fetchone()['count']
    conn.close()
    
    print("=" * 70)
    print(f"📊 INITIAL STATUS")
    print(f"   Total: {initial_total} | MercadoLibre: {initial_ml}")
    print("=" * 70)
    
    # Scrape with higher limits - cover more categories
    # pages_per_category=20 means 20*50 = 1000 listings per category scraped
    listings, stats = scraper.scrape_all(pages_per_category=20, max_listings=1000)
    
    print(f"\n✅ Scraped {len(listings)} listings")
    
    if listings:
        print(f"💾 Storing in database...")
        stored = scraper.store_in_database(listings)
        print(f"   ✓ Stored {stored} listings")
    
    # Final stats
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM listings')
    final_total = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
    final_ml = cursor.fetchone()['count']
    
    # Get breakdown by type
    cursor.execute('''
        SELECT property_type, listing_type, COUNT(*) as count
        FROM listings
        WHERE source = "mercadolibre"
        GROUP BY property_type, listing_type
        ORDER BY count DESC
    ''')
    breakdown = cursor.fetchall()
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"🎯 FINAL STATUS")
    print(f"   Total: {final_total} (+{final_total - initial_total})")
    print(f"   MercadoLibre: {final_ml} (+{final_ml - initial_ml})")
    print(f"\n   Breakdown:")
    for row in breakdown:
        print(f"      {row['listing_type']:<10} {row['property_type']:<15} {row['count']:>4}")
    print("=" * 70)
    
    if final_ml >= 500:
        print(f"\n🎉 SUCCESS! Reached 500+ MercadoLibre listings target!")
    else:
        print(f"\n⚠️  Need {500 - final_ml} more listings to reach 500+ target")
    
    return final_ml

if __name__ == '__main__':
    main()
