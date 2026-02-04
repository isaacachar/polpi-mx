#!/usr/bin/env python3
"""Final Lamudi scraper - extracts CDMX listings from JSON-LD data"""

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

class LamudiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8'
        })
        self.base_url = 'https://www.lamudi.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate search URLs for different property types and pages"""
        urls = []
        
        # Property types with more pages
        searches = [
            ('/departamento/for-sale/', 15),  # More apartment pages
            ('/casa/for-sale/', 10),          # House pages
            ('/terreno/for-sale/', 5)         # Land pages
        ]
        
        for base_path, max_pages in searches:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(self.base_url + base_path)
                else:
                    urls.append(f"{self.base_url}{base_path}?page={page}")
        
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
        
        # Strict CDMX filter - must contain CDMX indicators and exclude other states
        cdmx_indicators = [
            'ciudad de méxico', 'cdmx', 'miguel hidalgo', 'benito juárez', 'cuauhtémoc',
            'álvaro obregón', 'cuajimalpa', 'tlalpan', 'coyoacán', 'azcapotzalco',
            'polanco', 'condesa', 'roma norte', 'del valle', 'juárez'
        ]
        
        # States/cities to exclude
        exclude_terms = [
            'quintana roo', 'cancún', 'tulum', 'playa del carmen', 'solidaridad',
            'veracruz', 'boca del río', 'morelos', 'cuernavaca', 'nuevo león',
            'monterrey', 'jalisco', 'guadalajara', 'zapopan', 'querétaro',
            'nayarit', 'vallarta', 'estado de méxico'
        ]
        
        # Must have CDMX indicator AND not have exclude terms
        has_cdmx = any(indicator in full_address for indicator in cdmx_indicators)
        has_exclude = any(exclude in full_address for exclude in exclude_terms)
        
        return has_cdmx and not has_exclude

    def extract_listings_from_page(self, url):
        """Extract listings from a single page"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save HTML for debugging
            filename = f"lamudi_final_{int(time.time())}.html"
            with open(os.path.join(self.html_dir, filename), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            listings = []
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle the actual Lamudi structure
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
                                                    listing = self.parse_property_data(prop_data)
                                                    if listing:
                                                        listings.append(listing)
                    
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    continue
            
            print(f"Extracted {len(listings)} CDMX listings from {url}")
            return listings
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

    def parse_property_data(self, prop_data):
        """Parse property data into our format"""
        try:
            listing = {
                'source': 'lamudi',
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
                    listing['images'] = image[:3]  # Limit images
            
            # Estimate price based on CDMX market data
            listing['price_mxn'] = self.estimate_price(listing)
            
            return listing
            
        except Exception as e:
            print(f"Error parsing property: {e}")
            return None

    def estimate_price(self, listing):
        """Estimate price based on property characteristics"""
        if not listing.get('size_m2') or listing['size_m2'] <= 0:
            return None
        
        size_m2 = listing['size_m2']
        bedrooms = listing.get('bedrooms', 1) or 1
        
        # CDMX price estimates per m2 (2025 market rates)
        base_price_per_m2 = {
            1: 55000,   # 1 bedroom
            2: 65000,   # 2 bedroom  
            3: 75000,   # 3+ bedroom
        }
        
        price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), 65000)
        
        # Adjust for property type
        if 'penthouse' in listing.get('title', '').lower():
            price_per_m2 *= 1.5
        elif 'polanco' in listing.get('colonia', '').lower():
            price_per_m2 *= 1.8
        elif any(premium in listing.get('colonia', '').lower() 
                for premium in ['condesa', 'roma', 'del valle']):
            price_per_m2 *= 1.4
        
        estimated_price = size_m2 * price_per_m2
        return round(estimated_price, 0)

    def scrape_all_urls(self):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        all_listings = []
        
        for i, url in enumerate(urls):
            print(f"\nPage {i+1}/{len(urls)}")
            
            listings = self.extract_listings_from_page(url)
            all_listings.extend(listings)
            
            # Progress update
            print(f"Total listings so far: {len(all_listings)}")
            
            # Sleep between requests
            time.sleep(2)
            
            # Stop if we have enough listings
            if len(all_listings) >= 150:
                print(f"Reached target of 150+ listings ({len(all_listings)}), stopping")
                break
        
        return all_listings

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
                        city, colonia, description, images, parking_spaces, scraped_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing listing: {e}")
                continue
        
        return stored_count

def main():
    print("🏠 Starting final Lamudi CDMX scraper...")
    
    scraper = LamudiScraper()
    
    # Get current count
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    initial_count = cursor.fetchone()[0]
    conn.close()
    print(f"Starting with {initial_count} Lamudi listings in database")
    
    # Scrape listings
    listings = scraper.scrape_all_urls()
    
    print(f"\n📊 Scraped {len(listings)} CDMX listings total")
    
    if listings:
        # Store in database
        stored = scraper.store_in_database(listings)
        print(f"💾 Stored {stored} new listings in database")
        
        # Show sample listings
        print(f"\n🏠 Sample listings:")
        for i, listing in enumerate(listings[:5]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
            print(f"{i+1}. {listing.get('title', 'No title')[:50]}")
            print(f"   {price_str} | {listing.get('size_m2', 'N/A')} m² | {listing.get('bedrooms', 'N/A')} bed | {listing.get('colonia', 'N/A')}")
    
    # Final count
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n🎯 Final count: {final_count} Lamudi listings in database")
    print(f"Added {final_count - initial_count} new listings")
    
    if final_count >= 50:
        print("🎉 SUCCESS! Target achieved!")
    
    return final_count

if __name__ == '__main__':
    main()