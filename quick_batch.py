#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')

from lamudi_final_scraper import LamudiScraper
from database import PolpiDB

print('🚀 Running quick batch scraper...')

scraper = LamudiScraper()

# Target pages with good listings
urls = [
    'https://www.lamudi.com.mx/departamento/for-sale/',
    'https://www.lamudi.com.mx/departamento/for-sale/?page=2',
    'https://www.lamudi.com.mx/departamento/for-sale/?page=3',
    'https://www.lamudi.com.mx/departamento/for-sale/?page=4',
    'https://www.lamudi.com.mx/departamento/for-sale/?page=5',
    'https://www.lamudi.com.mx/casa/for-sale/',
    'https://www.lamudi.com.mx/casa/for-sale/?page=2',
    'https://www.lamudi.com.mx/casa/for-sale/?page=3'
]

all_listings = []

for i, url in enumerate(urls):
    print(f'\nPage {i+1}/{len(urls)}: {url.split("?")[0]}')
    
    try:
        listings = scraper.extract_listings_from_page(url)
        all_listings.extend(listings)
        print(f'Got {len(listings)} listings, total: {len(all_listings)}')
        
        time.sleep(2)  # Be nice to the server
        
    except Exception as e:
        print(f'Error on page {i+1}: {e}')
        continue

print(f'\n📊 Total scraped: {len(all_listings)} CDMX listings')

if all_listings:
    stored = scraper.store_in_database(all_listings)
    print(f'💾 Stored {stored} listings in database')
    
    # Show samples
    print(f'\n🏠 Sample listings:')
    for i, listing in enumerate(all_listings[:5]):
        title = listing.get('title', 'No title')[:50]
        price = listing.get('price_mxn', 0)
        size = listing.get('size_m2', 0)
        beds = listing.get('bedrooms', 'N/A')
        location = listing.get('colonia', 'Unknown')
        
        print(f'{i+1}. {title}')
        if price > 0:
            print(f'   ${price:,.0f} | {size} m² | {beds} bed(s) | {location}')
        else:
            print(f'   Price N/A | {size} m² | {beds} bed(s) | {location}')

# Check final database count
db = PolpiDB()
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
final_count = cursor.fetchone()[0]
conn.close()

print(f'\n🎯 Final database count: {final_count} Lamudi listings')

if final_count >= 100:
    print('🎉 SUCCESS! Achieved 100+ real CDMX listings!')
elif final_count >= 50:
    print('✅ GOOD! Achieved 50+ real CDMX listings!')
else:
    print('⚠️ Need more listings - consider running more pages')