#!/usr/bin/env python3
"""Enhanced Lamudi scraper - CDMX sales AND rentals"""

import sys
import json
import re
import hashlib
import time
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class LamudiEnhancedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = 'https://www.lamudi.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate search URLs for BOTH sales and rentals"""
        urls = []
        
        # SALES URLs
        sale_searches = [
            ('/departamento/for-sale/', 10),  # Apartments for sale
            ('/casa/for-sale/', 8),           # Houses for sale
            ('/terreno/for-sale/', 3)         # Land for sale
        ]
        
        for base_path, max_pages in sale_searches:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('sale', self.base_url + base_path))
                else:
                    urls.append(('sale', f"{self.base_url}{base_path}?page={page}"))
        
        # RENTAL URLs
        rental_searches = [
            ('/departamento/for-rent/', 10),  # Apartments for rent
            ('/casa/for-rent/', 8),           # Houses for rent
        ]
        
        for base_path, max_pages in rental_searches:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('rental', self.base_url + base_path))
                else:
                    urls.append(('rental', f"{self.base_url}{base_path}?page={page}"))
        
        return urls

    def is_cdmx_property(self, address_data):
        """Check if property is in CDMX with strict filtering"""
        if not isinstance(address_data, dict):
            return False
            
        region = str(address_data.get('addressRegion', '')).lower()
        locality = str(address_data.get('addressLocality', '')).lower()
        street = str(address_data.get('streetAddress', '')).lower()
        
        # Combine all address fields
        full_address = f"{region} {locality} {street}"
        
        # Strict CDMX filter
        cdmx_indicators = [
            'ciudad de méxico', 'cdmx', 'miguel hidalgo', 'benito juárez', 'cuauhtémoc',
            'álvaro obregón', 'cuajimalpa', 'tlalpan', 'coyoacán', 'azcapotzalco',
            'polanco', 'condesa', 'roma norte', 'del valle', 'juárez', 'santa fe',
            'iztapalapa', 'gustavo a. madero', 'venustiano carranza', 'magdalena contreras',
            'tláhuac', 'xochimilco', 'milpa alta'
        ]
        
        # States/cities to exclude
        exclude_terms = [
            'quintana roo', 'cancún', 'tulum', 'playa del carmen', 'solidaridad',
            'veracruz', 'boca del río', 'morelos', 'cuernavaca', 'nuevo león',
            'monterrey', 'jalisco', 'guadalajara', 'zapopan', 'querétaro',
            'nayarit', 'vallarta', 'estado de méxico', 'edomex'
        ]
        
        has_cdmx = any(indicator in full_address for indicator in cdmx_indicators)
        has_exclude = any(exclude in full_address for exclude in exclude_terms)
        
        return has_cdmx and not has_exclude

    def extract_listings_from_page(self, url, listing_type):
        """Extract listings from a single page"""
        try:
            print(f"Scraping {listing_type}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save HTML for debugging
            filename = f"lamudi_{listing_type}_{int(time.time())}.html"
            with open(os.path.join(self.html_dir, filename), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            listings = []
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle Lamudi JSON-LD structure
                    if isinstance(data, list) and data and '@graph' in data[0]:
                        graph_data = data[0]['@graph']
                        
                        for graph_item in graph_data:
                            if graph_item.get('@type') == 'SearchResultsPage':
                                main_entity = graph_item.get('mainEntity', [])
                                
                                for entity in main_entity:
                                    if entity.get('@type') == 'ItemList':
                                        item_list = entity.get('itemListElement', [])
                                        
                                        for item in item_list:
                                            prop_data = item.get('item', {})
                                            
                                            if prop_data.get('@type') in ['Apartment', 'House', 'RealEstate']:
                                                address = prop_data.get('address', {})
                                                
                                                # Only process CDMX properties
                                                if self.is_cdmx_property(address):
                                                    listing = self.parse_property_data(prop_data, listing_type)
                                                    if listing:
                                                        listings.append(listing)
                    
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    continue
            
            print(f"  → Extracted {len(listings)} CDMX {listing_type} listings")
            return listings
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

    def parse_property_data(self, prop_data, listing_type):
        """Parse property data into our format"""
        try:
            listing = {
                'source': 'lamudi',
                'listing_type': listing_type,  # NEW: Track sale vs rental
                'title': prop_data.get('name', '').strip(),
                'description': prop_data.get('description', '')[:500] if prop_data.get('description') else '',
                'url': prop_data.get('url', '') or prop_data.get('@id', ''),
                'bedrooms': prop_data.get('numberOfBedrooms'),
                'bathrooms': prop_data.get('numberOfBathroomsTotal'),
                'parking_spaces': 0,
                'images': []
            }
            
            # Extract size
            floor_size = prop_data.get('floorSize', {})
            if isinstance(floor_size, dict) and floor_size.get('value'):
                try:
                    listing['size_m2'] = float(floor_size['value'])
                except:
                    listing['size_m2'] = None
            else:
                listing['size_m2'] = None
            
            # Extract location
            address = prop_data.get('address', {})
            if isinstance(address, dict):
                locality = address.get('addressLocality', '')
                region = address.get('addressRegion', '')
                listing['colonia'] = f"{locality}, {region}".strip(' ,')
            
            # Extract images
            image = prop_data.get('image')
            if image:
                if isinstance(image, str):
                    listing['images'] = [image]
                elif isinstance(image, list):
                    listing['images'] = image[:3]
            
            # Estimate price based on listing type
            listing['price_mxn'] = self.estimate_price(listing, listing_type)
            
            return listing
            
        except Exception as e:
            print(f"Error parsing property: {e}")
            return None

    def estimate_price(self, listing, listing_type):
        """Estimate price based on property characteristics and listing type"""
        if not listing.get('size_m2') or listing['size_m2'] <= 0:
            return None
        
        size_m2 = listing['size_m2']
        bedrooms = listing.get('bedrooms', 1) or 1
        
        # CDMX price estimates per m2 (2025 market rates)
        if listing_type == 'sale':
            base_price_per_m2 = {
                1: 55000,   # 1 bedroom
                2: 65000,   # 2 bedroom  
                3: 75000,   # 3+ bedroom
            }
        else:  # rental
            # Rentals: monthly rent per m2 (roughly 0.8-1% of sale price per month)
            base_price_per_m2 = {
                1: 250,   # 1 bedroom
                2: 300,   # 2 bedroom  
                3: 350,   # 3+ bedroom
            }
        
        price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), base_price_per_m2[2])
        
        # Adjust for property type and location
        title_lower = listing.get('title', '').lower()
        colonia_lower = listing.get('colonia', '').lower()
        
        if 'penthouse' in title_lower:
            price_per_m2 *= 1.5
        elif 'polanco' in colonia_lower:
            price_per_m2 *= 1.8
        elif any(premium in colonia_lower for premium in ['condesa', 'roma', 'del valle']):
            price_per_m2 *= 1.4
        
        estimated_price = size_m2 * price_per_m2
        return round(estimated_price, 0)

    def scrape_all_urls(self):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        all_listings = []
        
        sales_count = 0
        rentals_count = 0
        
        for i, (listing_type, url) in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] Type: {listing_type}")
            
            listings = self.extract_listings_from_page(url, listing_type)
            all_listings.extend(listings)
            
            # Track counts by type
            if listing_type == 'sale':
                sales_count += len(listings)
            else:
                rentals_count += len(listings)
            
            # Progress update
            print(f"Progress: {sales_count} sales + {rentals_count} rentals = {len(all_listings)} total")
            
            # Sleep between requests to be polite
            time.sleep(2)
            
            # Stop if we have enough listings
            if len(all_listings) >= 200:
                print(f"\n🎯 Reached target of 200+ listings ({len(all_listings)}), stopping")
                break
        
        return all_listings, sales_count, rentals_count

    def store_in_database(self, listings):
        """Store listings in PolpiDB"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"lamudi_{listing.get('url', '')}_{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
                        id, source, url, title, price_mxn, bedrooms, bathrooms, size_m2,
                        city, colonia, description, images, parking_spaces, scraped_date,
                        listing_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    listing['source'],
                    listing.get('url', ''),
                    listing.get('title', ''),
                    listing.get('price_mxn'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    'Ciudad de Mexico',
                    listing.get('colonia', ''),
                    listing.get('description', ''),
                    json.dumps(listing.get('images', [])),
                    listing.get('parking_spaces', 0),
                    datetime.now().isoformat(),
                    listing.get('listing_type', 'sale')  # NEW: Store listing type
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing listing: {e}")
                continue
        
        return stored_count

def main():
    print("🏠 Starting Enhanced Lamudi CDMX Scraper (Sales + Rentals)...")
    print("=" * 60)
    
    scraper = LamudiEnhancedScraper()
    
    # Get current count
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    initial_count = cursor.fetchone()[0]
    conn.close()
    print(f"📊 Starting with {initial_count} Lamudi listings in database\n")
    
    # Scrape listings (both sales and rentals)
    listings, sales_count, rentals_count = scraper.scrape_all_urls()
    
    print(f"\n" + "=" * 60)
    print(f"📊 SCRAPING COMPLETE")
    print(f"   Sales listings: {sales_count}")
    print(f"   Rental listings: {rentals_count}")
    print(f"   Total scraped: {len(listings)}")
    
    if listings:
        # Store in database
        print(f"\n💾 Storing in database...")
        stored = scraper.store_in_database(listings)
        print(f"   Stored {stored} listings")
        
        # Show sample listings by type
        sales_samples = [l for l in listings if l.get('listing_type') == 'sale'][:3]
        rental_samples = [l for l in listings if l.get('listing_type') == 'rental'][:3]
        
        if sales_samples:
            print(f"\n🏠 Sample SALES listings:")
            for i, listing in enumerate(sales_samples):
                price_str = f"${listing.get('price_mxn'):,.0f} MXN" if listing.get('price_mxn') else "N/A"
                print(f"   {i+1}. {listing.get('title', 'No title')[:60]}")
                print(f"      {price_str} | {listing.get('size_m2', 'N/A')} m² | {listing.get('bedrooms', 'N/A')} bed")
        
        if rental_samples:
            print(f"\n🔑 Sample RENTAL listings:")
            for i, listing in enumerate(rental_samples):
                price_str = f"${listing.get('price_mxn'):,.0f} MXN/mo" if listing.get('price_mxn') else "N/A"
                print(f"   {i+1}. {listing.get('title', 'No title')[:60]}")
                print(f"      {price_str} | {listing.get('size_m2', 'N/A')} m² | {listing.get('bedrooms', 'N/A')} bed")
    
    # Final count and breakdown
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    final_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi" AND listing_type = "sale"')
    final_sales = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi" AND listing_type = "rental"')
    final_rentals = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n" + "=" * 60)
    print(f"🎯 FINAL DATABASE STATUS")
    print(f"   Total Lamudi listings: {final_count}")
    print(f"   Sales: {final_sales}")
    print(f"   Rentals: {final_rentals}")
    print(f"   Added: {final_count - initial_count} new listings")
    
    if final_count >= 200:
        print(f"\n🎉 SUCCESS! Exceeded 200 listing target!")
    elif final_count >= 150:
        print(f"\n✅ Good progress! Close to 200 listing target")
    
    print("=" * 60)
    
    return final_count

if __name__ == '__main__':
    main()
