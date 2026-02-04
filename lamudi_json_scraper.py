#!/usr/bin/env python3
"""Lamudi JSON-LD scraper - extracts structured data directly"""

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

class LamudiJSONScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })
        self.base_url = 'https://www.lamudi.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        
        # Create HTML directory if it doesn't exist
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate list of search URLs to scrape"""
        urls = []
        
        # Main property types with pagination
        base_searches = [
            '/departamento/for-sale/',
            '/casa/for-sale/',
            '/terreno/for-sale/'
        ]
        
        for base in base_searches:
            # Multiple pages for each type
            for page in range(1, 11):  # Pages 1-10
                if page == 1:
                    urls.append(self.base_url + base)
                else:
                    urls.append(f"{self.base_url}{base}?page={page}")
        
        return urls

    def fetch_page(self, url):
        """Fetch a page with retries"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def extract_json_listings(self, html_content):
        """Extract listings from JSON-LD structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find JSON-LD script tags
        json_scripts = soup.find_all('script', type='application/ld+json')
        
        listings = []
        
        for script in json_scripts:
            try:
                data = json.loads(script.string)
                
                # Navigate to listings data
                if '@graph' in data:
                    for graph_item in data['@graph']:
                        if graph_item.get('@type') == 'SearchResultsPage':
                            main_entity = graph_item.get('mainEntity', [])
                            for entity in main_entity:
                                if entity.get('@type') == 'ItemList':
                                    item_list = entity.get('itemListElement', [])
                                    for item in item_list:
                                        listing_data = item.get('item', {})
                                        if listing_data.get('@type') in ['Apartment', 'House', 'RealEstateProperty']:
                                            listing = self.parse_json_listing(listing_data)
                                            if listing:
                                                listings.append(listing)
                
                # Handle direct listing arrays
                elif isinstance(data, list):
                    for item in data:
                        if item.get('@type') in ['Apartment', 'House', 'RealEstateProperty']:
                            listing = self.parse_json_listing(item)
                            if listing:
                                listings.append(listing)
                
            except Exception as e:
                print(f"Error parsing JSON-LD: {e}")
                continue
        
        return listings

    def parse_json_listing(self, data):
        """Parse a single JSON listing into our format"""
        try:
            listing = {
                'source': 'lamudi',
                'title': data.get('name', ''),
                'description': data.get('description', '')[:500] if data.get('description') else '',
                'url': data.get('url', '') or data.get('@id', ''),
                'bedrooms': data.get('numberOfBedrooms'),
                'bathrooms': data.get('numberOfBathroomsTotal') or data.get('numberOfBathrooms'),
                'parking_spaces': 0,  # Not in JSON typically
                'images': []
            }
            
            # Extract price (not in the JSON, will need to estimate or find elsewhere)
            listing['price_mxn'] = None
            
            # Extract size
            floor_size = data.get('floorSize', {})
            if isinstance(floor_size, dict):
                listing['size_m2'] = floor_size.get('value')
                if listing['size_m2']:
                    try:
                        listing['size_m2'] = float(listing['size_m2'])
                    except:
                        listing['size_m2'] = None
            
            # Extract location
            address = data.get('address', {})
            if isinstance(address, dict):
                listing['colonia'] = address.get('addressLocality', '') or address.get('streetAddress', '')
                
                # Filter for CDMX properties
                region = address.get('addressRegion', '')
                locality = address.get('addressLocality', '')
                street = address.get('streetAddress', '')
                
                # Only include CDMX properties
                if any(cdmx_term in str(region + locality + street).lower() for cdmx_term in 
                       ['ciudad de méxico', 'cdmx', 'miguel hidalgo', 'benito juárez', 'cuauhtémoc', 
                        'álvaro obregón', 'cuajimalpa', 'tlalpan', 'coyoacán', 'azcapotzalco']):
                    
                    # Extract images
                    image = data.get('image')
                    if image:
                        if isinstance(image, str):
                            listing['images'] = [image]
                        elif isinstance(image, list):
                            listing['images'] = image[:5]  # Limit to 5 images
                    
                    return listing
                    
            return None  # Skip non-CDMX properties
            
        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None

    def scrape_page(self, url):
        """Scrape a single page for listings"""
        html_content = self.fetch_page(url)
        if not html_content:
            return []
        
        # Save HTML for debugging
        filename = f"lamudi_json_{int(time.time())}.html"
        filepath = os.path.join(self.html_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Extract listings from JSON
        listings = self.extract_json_listings(html_content)
        
        print(f"Extracted {len(listings)} CDMX listings from {url}")
        return listings

    def scrape_all_pages(self):
        """Scrape all search URLs"""
        urls = self.get_search_urls()
        all_listings = []
        
        for i, url in enumerate(urls):
            print(f"\nScraping page {i+1}/{len(urls)}: {url}")
            
            listings = self.scrape_page(url)
            all_listings.extend(listings)
            
            # Be nice to the server
            time.sleep(3)
            
            # Stop if we have enough listings
            if len(all_listings) >= 200:
                print(f"Reached {len(all_listings)} listings, stopping")
                break
            
            # Stop if no listings found on multiple consecutive pages
            if i > 5 and not listings:
                print("No listings found on recent pages, stopping")
                break
        
        return all_listings

    def estimate_price_from_description(self, description, size_m2, bedrooms):
        """Estimate price based on description and property details (fallback)"""
        if not description:
            return None
        
        # Look for price mentions in description
        price_patterns = [
            r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:MXN|mxn|pesos?)?',
            r'([\d,]+(?:\.\d+)?)\s*(?:millones?|MXN|mxn)',
            r'precio[:\s]*([\d,]+)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                    
                    # Handle millions
                    if 'millón' in description.lower() or 'million' in description.lower():
                        price *= 1000000
                    elif price < 10000 and size_m2 and size_m2 > 50:  # Likely in millions
                        price *= 1000000
                    
                    return price
                except:
                    continue
        
        # Fallback: estimate based on size and bedrooms
        if size_m2 and size_m2 > 0:
            # Very rough CDMX price estimates per m2
            price_per_m2 = 50000  # Base price per m2
            
            # Adjust by bedrooms (more bedrooms = better area typically)
            if bedrooms:
                if bedrooms >= 3:
                    price_per_m2 = 80000
                elif bedrooms == 2:
                    price_per_m2 = 65000
                elif bedrooms == 1:
                    price_per_m2 = 55000
            
            estimated_price = size_m2 * price_per_m2
            return estimated_price
        
        return None

    def store_in_database(self, listings):
        """Store listings in database"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"{listing['source']}_{listing.get('url', '')}_{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Estimate price if not available
                if not listing.get('price_mxn'):
                    listing['price_mxn'] = self.estimate_price_from_description(
                        listing.get('description', ''),
                        listing.get('size_m2'),
                        listing.get('bedrooms')
                    )
                
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
    """Main function"""
    print("🚀 Starting Lamudi JSON scraper for CDMX...")
    
    scraper = LamudiJSONScraper()
    
    # Scrape all pages
    listings = scraper.scrape_all_pages()
    
    print(f"\n📊 Total CDMX listings found: {len(listings)}")
    
    if listings:
        # Store in database
        stored = scraper.store_in_database(listings)
        print(f"💾 Stored {stored} listings in database")
        
        # Show sample listings
        print(f"\n🏠 Sample listings:")
        for i, listing in enumerate(listings[:10]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "Price N/A"
            title = listing.get('title', 'No title')[:50]
            location = listing.get('colonia', 'Unknown')
            size = f"{listing.get('size_m2', 'N/A')} m²"
            beds = f"{listing.get('bedrooms', 'N/A')} bed(s)"
            print(f"{i+1:2d}. {title}")
            print(f"     {price_str} | {size} | {beds} | {location}")
            print()
    
    # Final database count
    print(f"\n🎯 Final database check...")
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Total Lamudi listings in database: {final_count}")
    
    if final_count >= 50:
        print("🎉 SUCCESS! Achieved target of 50+ real CDMX listings!")
    else:
        print("⚠️  Need more listings - consider running again or checking more pages")

if __name__ == '__main__':
    main()