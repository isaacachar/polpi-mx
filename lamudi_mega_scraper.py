#!/usr/bin/env python3
"""Comprehensive Lamudi scraper to get 200+ real CDMX property listings"""

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

class LamudiScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = 'https://www.lamudi.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        
        # Create HTML directory if it doesn't exist
        os.makedirs(self.html_dir, exist_ok=True)
        
        # Search configurations
        self.search_queries = [
            # Property types
            {'type': 'departamento', 'city': 'ciudad-de-mexico', 'pages': 10},
            {'type': 'casa', 'city': 'ciudad-de-mexico', 'pages': 10},
            {'type': 'terreno', 'city': 'ciudad-de-mexico', 'pages': 5},
            
            # Premium colonias
            {'type': 'departamento', 'city': 'polanco', 'pages': 5},
            {'type': 'departamento', 'city': 'condesa', 'pages': 5},
            {'type': 'departamento', 'city': 'roma-norte', 'pages': 5},
            {'type': 'departamento', 'city': 'del-valle', 'pages': 5},
            {'type': 'casa', 'city': 'coyoacan', 'pages': 3},
            {'type': 'casa', 'city': 'santa-fe', 'pages': 3},
            {'type': 'casa', 'city': 'san-angel', 'pages': 3},
            {'type': 'casa', 'city': 'lomas-de-chapultepec', 'pages': 3},
        ]

    def get_search_url(self, property_type, city, page=1):
        """Generate search URL for Lamudi"""
        if page == 1:
            return f"{self.base_url}/{city}/{property_type}/for-sale/"
        else:
            return f"{self.base_url}/{city}/{property_type}/for-sale/?page={page}"

    def save_html(self, content, filename):
        """Save HTML content to file for debugging"""
        filepath = os.path.join(self.html_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved HTML to {filename}")

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
                    time.sleep(5 * (attempt + 1))  # Progressive backoff
                else:
                    print(f"Failed to fetch {url} after {max_retries} attempts")
                    return None

    def extract_price(self, price_text):
        """Extract price from Mexican format text"""
        if not price_text:
            return None
        
        # Remove whitespace and normalize
        price_text = re.sub(r'\s+', ' ', price_text.strip())
        
        # Look for patterns like "$ 6,500,000 MXN" or "USD 2,070,000"
        if 'USD' in price_text.upper():
            # Convert USD to MXN (approximate rate 20:1)
            usd_match = re.search(r'USD\s*([\d,]+)', price_text, re.IGNORECASE)
            if usd_match:
                usd_price = float(usd_match.group(1).replace(',', ''))
                return usd_price * 20  # Approximate conversion
        
        # Look for MXN prices
        mxn_match = re.search(r'[$]?\s*([\d,]+)\s*(?:MXN|mxn)?', price_text)
        if mxn_match:
            return float(mxn_match.group(1).replace(',', ''))
        
        return None

    def extract_number(self, text):
        """Extract number from text"""
        if not text:
            return None
        match = re.search(r'(\d+)', str(text))
        return int(match.group(1)) if match else None

    def parse_listing_card(self, card_element):
        """Parse individual listing card from HTML"""
        try:
            listing = {}
            
            # Extract title
            title_elem = card_element.find(['h3', 'h2', 'a'], class_=re.compile(r'title|name|heading'))
            if not title_elem:
                title_elem = card_element.find('a')
            listing['title'] = title_elem.get_text(strip=True) if title_elem else 'No title'
            
            # Extract URL
            link_elem = card_element.find('a', href=True)
            if link_elem:
                listing['url'] = urljoin(self.base_url, link_elem['href'])
            else:
                listing['url'] = ''
            
            # Extract price
            price_elem = card_element.find(string=re.compile(r'[$]\s*[\d,]+'))
            if not price_elem:
                price_elem = card_element.find(class_=re.compile(r'price'))
            listing['price_mxn'] = self.extract_price(str(price_elem)) if price_elem else None
            
            # Extract bedrooms
            bedrooms_elem = card_element.find(string=re.compile(r'\d+\s*rec[áa]mara'))
            if not bedrooms_elem:
                bedrooms_elem = card_element.find(class_=re.compile(r'bedroom'))
            listing['bedrooms'] = self.extract_number(bedrooms_elem) if bedrooms_elem else None
            
            # Extract bathrooms
            bathrooms_elem = card_element.find(string=re.compile(r'\d+\s*ba[ñn]o'))
            if not bathrooms_elem:
                bathrooms_elem = card_element.find(class_=re.compile(r'bathroom'))
            listing['bathrooms'] = self.extract_number(bathrooms_elem) if bathrooms_elem else None
            
            # Extract size
            size_elem = card_element.find(string=re.compile(r'\d+\s*m[²2]'))
            if not size_elem:
                size_elem = card_element.find(class_=re.compile(r'size|area'))
            listing['size_m2'] = self.extract_number(size_elem) if size_elem else None
            
            # Extract location/colonia
            location_elem = card_element.find(class_=re.compile(r'location|address|area'))
            if not location_elem:
                location_elem = card_element.find(string=re.compile(r'Ciudad de México|CDMX|Álvaro Obregón|Benito Juárez'))
            listing['colonia'] = location_elem.get_text(strip=True) if location_elem else None
            
            # Extract description (if available)
            desc_elem = card_element.find(class_=re.compile(r'description|summary'))
            listing['description'] = desc_elem.get_text(strip=True)[:500] if desc_elem else None
            
            # Default values
            listing['source'] = 'lamudi'
            listing['parking_spaces'] = 0
            listing['images'] = []
            
            return listing if listing.get('title') != 'No title' else None
            
        except Exception as e:
            print(f"Error parsing listing card: {e}")
            return None

    def scrape_search_page(self, property_type, city, page=1):
        """Scrape a single search results page"""
        url = self.get_search_url(property_type, city, page)
        html_content = self.fetch_page(url)
        
        if not html_content:
            return []
        
        # Save HTML for debugging
        filename = f"lamudi_{property_type}_{city}_page{page}.html"
        self.save_html(html_content, filename)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find listing containers - try different patterns
        listing_cards = []
        
        # Common patterns for property listing containers
        patterns = [
            {'class': re.compile(r'card|listing|property|item')},
            {'class': re.compile(r'result')},
            '[data-testid*="listing"]',
            '.listing-card',
            '.property-card',
            '.search-result'
        ]
        
        for pattern in patterns:
            if isinstance(pattern, dict):
                cards = soup.find_all('div', pattern)
            else:
                cards = soup.select(pattern)
            
            if cards:
                listing_cards = cards
                print(f"Found {len(cards)} listing cards using pattern: {pattern}")
                break
        
        # Fallback: look for any div with property-like content
        if not listing_cards:
            all_divs = soup.find_all('div')
            listing_cards = []
            for div in all_divs:
                text = div.get_text()
                if ('recámara' in text or 'baño' in text or '$' in text) and len(text) > 100:
                    listing_cards.append(div)
            print(f"Fallback: Found {len(listing_cards)} potential listing divs")
        
        # Parse each listing
        listings = []
        for card in listing_cards:
            listing = self.parse_listing_card(card)
            if listing:
                listings.append(listing)
        
        print(f"Extracted {len(listings)} listings from {url}")
        return listings

    def scrape_all_pages(self):
        """Scrape all configured search queries and pages"""
        all_listings = []
        
        for query in self.search_queries:
            property_type = query['type']
            city = query['city']
            max_pages = query['pages']
            
            print(f"\nScraping {property_type} in {city} ({max_pages} pages)...")
            
            for page in range(1, max_pages + 1):
                listings = self.scrape_search_page(property_type, city, page)
                all_listings.extend(listings)
                
                # Be nice to the server
                time.sleep(2)
                
                # If no listings found, might have reached the end
                if not listings and page > 1:
                    print(f"No listings found on page {page}, stopping")
                    break
        
        return all_listings

    def store_in_database(self, listings):
        """Store listings in the PolpiDB database"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"{listing['source']}_{listing.get('url', '')}{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Convert images list to JSON string
                images_json = json.dumps(listing.get('images', []))
                
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
                    listing.get('url'),
                    listing.get('title'),
                    listing.get('price_mxn'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    'Ciudad de Mexico',  # city
                    listing.get('colonia'),
                    listing.get('description'),
                    images_json,
                    listing.get('parking_spaces', 0),
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing listing '{listing.get('title', 'Unknown')}': {e}")
                continue
        
        return stored_count

def main():
    """Main scraping function"""
    print("🏠 Starting Lamudi CDMX mega scraper...")
    
    scraper = LamudiScraper()
    
    # Scrape all configured queries
    all_listings = scraper.scrape_all_pages()
    
    print(f"\n📊 Total listings scraped: {len(all_listings)}")
    
    # Filter out empty/invalid listings
    valid_listings = [l for l in all_listings if l.get('title') and l.get('title') != 'No title']
    print(f"📝 Valid listings: {len(valid_listings)}")
    
    if valid_listings:
        # Store in database
        stored = scraper.store_in_database(valid_listings)
        print(f"💾 Stored {stored} listings in database")
        
        # Show samples
        print(f"\n🏠 Sample listings:")
        for i, listing in enumerate(valid_listings[:10]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
            title = listing.get('title', 'N/A')[:50]
            location = listing.get('colonia', 'N/A')
            print(f"{i+1:2d}. {title} - {price_str} - {location}")
    else:
        print("⚠️  No valid listings found")

if __name__ == '__main__':
    main()