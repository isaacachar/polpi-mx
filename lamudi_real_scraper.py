#!/usr/bin/env python3
"""Real Lamudi scraper with correct URL structure"""

import sys
import json
import re
import hashlib
import time
import requests
import os
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class LamudiRealScraper:
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
            # First page
            urls.append(self.base_url + base)
            # Subsequent pages
            for page in range(2, 11):  # Pages 2-10
                urls.append(f"{self.base_url}{base}?page={page}")
        
        return urls

    def fetch_page(self, url, max_retries=3):
        """Fetch a page with retries"""
        for attempt in range(max_retries):
            try:
                print(f"Fetching: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    print(f"Failed to fetch {url}")
                    return None

    def save_html(self, content, filename):
        """Save HTML content to file for debugging"""
        filepath = os.path.join(self.html_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
        
        # Look for patterns like "$1,500,000" or "1.5M"
        price_match = re.search(r'[$]?\s*([\d,]+(?:\.\d+)?)\s*(?:M|millones?|MXN)?', str(text), re.IGNORECASE)
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            price = float(price_str)
            
            # Handle millions
            if 'M' in str(text) or 'millón' in str(text).lower():
                price *= 1000000
                
            return price
        return None

    def extract_number(self, text):
        """Extract first number from text"""
        if not text:
            return None
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None

    def scrape_page_simple(self, url):
        """Simple approach: get page and find any divs with property-like content"""
        html_content = self.fetch_page(url)
        if not html_content:
            return []

        # Save for debugging
        filename = f"lamudi_page_{int(time.time())}.html"
        self.save_html(html_content, filename)

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for any text patterns that indicate properties
        listings = []
        all_text = soup.get_text()
        
        # Split by common separators and look for property-like entries
        sections = re.split(r'\n{2,}|\s{10,}', all_text)
        
        for section in sections:
            if len(section) > 50 and '$' in section:
                # Extract basic info from text block
                listing = self.parse_text_section(section)
                if listing:
                    listings.append(listing)
        
        print(f"Extracted {len(listings)} listings from {url}")
        return listings

    def parse_text_section(self, text):
        """Parse a text section to extract property information"""
        try:
            if len(text) < 30:
                return None
            
            # Basic property information
            listing = {
                'source': 'lamudi',
                'title': '',
                'price_mxn': None,
                'bedrooms': None,
                'bathrooms': None,
                'size_m2': None,
                'colonia': '',
                'description': text[:300],  # First 300 chars as description
                'url': '',
                'parking_spaces': 0,
                'images': []
            }
            
            # Extract price
            listing['price_mxn'] = self.extract_price(text)
            
            # Extract bedrooms (recámaras)
            bed_match = re.search(r'(\d+)\s*(?:rec[aá]maras?|habitacion|dormitorio)', text, re.IGNORECASE)
            listing['bedrooms'] = int(bed_match.group(1)) if bed_match else None
            
            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*(?:ba[ñn]os?)', text, re.IGNORECASE)
            listing['bathrooms'] = int(bath_match.group(1)) if bath_match else None
            
            # Extract size
            size_match = re.search(r'(\d+)\s*m[²2]', text, re.IGNORECASE)
            listing['size_m2'] = int(size_match.group(1)) if size_match else None
            
            # Extract title (first meaningful line)
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
            if lines:
                listing['title'] = lines[0][:100]
            
            # Extract location/colonia
            location_keywords = ['Ciudad de México', 'CDMX', 'Polanco', 'Condesa', 'Roma', 'Del Valle', 'Coyoacán', 'Santa Fe']
            for keyword in location_keywords:
                if keyword.lower() in text.lower():
                    listing['colonia'] = keyword
                    break
            
            # Only return if we have meaningful data
            if listing['price_mxn'] or listing['bedrooms'] or 'departamento' in text.lower() or 'casa' in text.lower():
                return listing
                
        except Exception as e:
            print(f"Error parsing text section: {e}")
            
        return None

    def scrape_all_urls(self):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        all_listings = []
        
        for i, url in enumerate(urls):
            print(f"\nScraping {i+1}/{len(urls)}: {url}")
            
            listings = self.scrape_page_simple(url)
            all_listings.extend(listings)
            
            # Be nice to the server
            time.sleep(2)
            
            # Stop if we get enough listings
            if len(all_listings) > 200:
                print(f"Reached {len(all_listings)} listings, stopping")
                break
        
        return all_listings

    def store_in_database(self, listings):
        """Store listings in database"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"{listing['source']}_{listing.get('title', '')}_{listing.get('price_mxn', 0)}"
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
    """Main function"""
    print("🚀 Starting enhanced Lamudi scraper...")
    
    scraper = LamudiRealScraper()
    
    # Scrape all URLs
    listings = scraper.scrape_all_urls()
    
    print(f"\n📊 Total listings found: {len(listings)}")
    
    # Filter valid listings
    valid_listings = [l for l in listings if l.get('price_mxn') or l.get('bedrooms')]
    print(f"📝 Valid listings: {len(valid_listings)}")
    
    if valid_listings:
        # Store in database
        stored = scraper.store_in_database(valid_listings)
        print(f"💾 Stored {stored} listings in database")
        
        # Show sample listings
        print(f"\n🏠 Sample listings:")
        for i, listing in enumerate(valid_listings[:10]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
            title = listing.get('title', 'No title')[:50]
            beds = listing.get('bedrooms', 'N/A')
            print(f"{i+1:2d}. {title} - {price_str} - {beds} bed(s)")
    
    # Final count
    print(f"\n🎯 Final database check...")
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Total Lamudi listings in database: {final_count}")

if __name__ == '__main__':
    main()