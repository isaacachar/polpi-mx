#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')

from lamudi_final_scraper import LamudiScraper

print('Testing scraper with one page...')
scraper = LamudiScraper()

# Test just the department page
url = 'https://www.lamudi.com.mx/departamento/for-sale/'
listings = scraper.extract_listings_from_page(url)

print(f'Found {len(listings)} CDMX listings from test page')

if listings:
    print('Sample listings:')
    for i, listing in enumerate(listings[:3]):
        title = listing.get('title', 'No title')[:50]
        size = listing.get('size_m2', 'N/A')
        beds = listing.get('bedrooms', 'N/A')
        location = listing.get('colonia', 'Unknown')
        
        print(f'{i+1}. {title}')
        print(f'   Size: {size} m² | Beds: {beds} | Location: {location}')
        
        price = listing.get('price_mxn')
        if price:
            print(f'   Estimated price: ${price:,.0f}')
        else:
            print('   No price estimated')
        print()

# Store a few in database
if listings:
    stored = scraper.store_in_database(listings[:5])  # Just store first 5
    print(f'Stored {stored} listings in database for testing')