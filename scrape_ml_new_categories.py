#!/usr/bin/env python3
"""Scrape MercadoLibre categories that are underrepresented in the database"""

import sys
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')

from mercadolibre_improved_scraper import MercadoLibreImprovedScraper
from database import PolpiDB

def main():
    scraper = MercadoLibreImprovedScraper()
    
    # Custom URLs focused on underrepresented categories
    custom_urls = []
    
    # 1. Casas en renta (rental houses) - not in DB at all
    for page in range(1, 21):  # 20 pages
        offset = (page - 1) * 50
        if offset == 0:
            url = f"{scraper.base_url}/casas/renta/distrito-federal/"
        else:
            url = f"{scraper.base_url}/casas/renta/distrito-federal/_Desde_{offset}"
        
        custom_urls.append({
            'url': url,
            'listing_type': 'rental',
            'property_type': 'casa',
            'page': page,
            'category': 'rental_casa'
        })
    
    # 2. Terrenos (land) - not in DB at all
    for page in range(1, 11):  # 10 pages
        offset = (page - 1) * 50
        if offset == 0:
            url = f"{scraper.base_url}/terrenos/venta/distrito-federal/"
        else:
            url = f"{scraper.base_url}/terrenos/venta/distrito-federal/_Desde_{offset}"
        
        custom_urls.append({
            'url': url,
            'listing_type': 'sale',
            'property_type': 'terreno',
            'page': page,
            'category': 'sale_terreno'
        })
    
    # 3. More rental apartments (only 48 in DB)
    for page in range(1, 16):  # 15 pages
        offset = (page - 1) * 50
        if offset == 0:
            url = f"{scraper.base_url}/departamentos/renta/distrito-federal/"
        else:
            url = f"{scraper.base_url}/departamentos/renta/distrito-federal/_Desde_{offset}"
        
        custom_urls.append({
            'url': url,
            'listing_type': 'rental',
            'property_type': 'departamento',
            'page': page,
            'category': 'rental_departamento'
        })
    
    # 4. More houses for sale (only 48 in DB)
    for page in range(1, 16):  # 15 pages
        offset = (page - 1) * 50
        if offset == 0:
            url = f"{scraper.base_url}/casas/venta/distrito-federal/"
        else:
            url = f"{scraper.base_url}/casas/venta/distrito-federal/_Desde_{offset}"
        
        custom_urls.append({
            'url': url,
            'listing_type': 'sale',
            'property_type': 'casa',
            'page': page,
            'category': 'sale_casa'
        })
    
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
    print(f"📊 INITIAL DATABASE")
    print(f"   Total: {initial_total} | MercadoLibre: {initial_ml}")
    print("=" * 70)
    print(f"\n🎯 TARGETING UNDERREPRESENTED CATEGORIES")
    print(f"   - Rental houses (casas renta): 0 in DB")
    print(f"   - Land (terrenos): 0 in DB")
    print(f"   - Rental apartments: 48 in DB")
    print(f"   - Houses for sale: 48 in DB")
    print(f"\n   Total pages to scrape: {len(custom_urls)}\n")
    
    # Scrape
    all_listings = []
    stats_by_category = {}
    
    for i, search_info in enumerate(custom_urls):
        print(f"[{i+1}/{len(custom_urls)}]", end=" ")
        
        listings = scraper.scrape_page(search_info)
        all_listings.extend(listings)
        
        category = search_info['category']
        stats_by_category[category] = stats_by_category.get(category, 0) + len(listings)
        
        print(f"    Total: {len(all_listings)}")
        
        import time
        time.sleep(2)
    
    print("\n" + "=" * 70)
    print(f"📊 SCRAPED {len(all_listings)} LISTINGS")
    for category, count in sorted(stats_by_category.items()):
        print(f"   {category}: {count}")
    print("=" * 70)
    
    if all_listings:
        print(f"\n💾 Storing in database...")
        stored = scraper.store_in_database(all_listings)
        print(f"   ✓ Stored {stored} listings")
    
    # Final stats
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM listings')
    final_total = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
    final_ml = cursor.fetchone()['count']
    
    # Breakdown by type
    cursor.execute("""
        SELECT property_type, listing_type, COUNT(*) as count 
        FROM listings 
        WHERE source='mercadolibre' 
        GROUP BY property_type, listing_type 
        ORDER BY property_type, listing_type
    """)
    breakdown = cursor.fetchall()
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"🎯 FINAL DATABASE")
    print(f"   Total: {final_total} (+{final_total - initial_total})")
    print(f"   MercadoLibre: {final_ml} (+{final_ml - initial_ml})")
    print(f"\n   Breakdown:")
    for row in breakdown:
        print(f"      {row['property_type']} {row['listing_type']}: {row['count']}")
    print("=" * 70)

if __name__ == '__main__':
    main()
