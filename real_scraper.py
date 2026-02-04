#!/usr/bin/env python3
"""Real estate scraper for CDMX - REAL DATA ONLY"""

import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import time
import re
import sys
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealEstateScraper:
    def __init__(self):
        self.db = PolpiDB()
        self.session = requests.Session()
        self.cloudscraper_session = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(self.headers)
        
    def save_html(self, content, filename):
        """Save HTML content to data/html directory"""
        filepath = f"data/html/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved HTML to {filepath}")
        
    def test_url_access(self, url, site_name):
        """Test if we can access a URL and save the response"""
        logger.info(f"Testing access to {site_name}: {url}")
        
        # Try with regular requests first
        try:
            response = self.session.get(url, timeout=30)
            logger.info(f"Regular requests - Status: {response.status_code}")
            
            if response.status_code == 200:
                self.save_html(response.text, f"{site_name}_regular.html")
                return response.text, 'regular'
            elif response.status_code == 403:
                logger.warning(f"403 Forbidden with regular requests, trying cloudscraper...")
            else:
                logger.warning(f"Status {response.status_code} with regular requests")
                
        except Exception as e:
            logger.error(f"Regular requests failed: {e}")
            
        # Try with cloudscraper if regular requests failed
        try:
            response = self.cloudscraper_session.get(url, timeout=30)
            logger.info(f"Cloudscraper - Status: {response.status_code}")
            
            if response.status_code == 200:
                self.save_html(response.text, f"{site_name}_cloudscraper.html")
                return response.text, 'cloudscraper'
            else:
                logger.error(f"Cloudscraper also failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Cloudscraper failed: {e}")
            
        # Try with Google referer
        try:
            headers_with_referer = self.headers.copy()
            headers_with_referer['Referer'] = 'https://www.google.com/'
            response = self.session.get(url, headers=headers_with_referer, timeout=30)
            logger.info(f"With Google referer - Status: {response.status_code}")
            
            if response.status_code == 200:
                self.save_html(response.text, f"{site_name}_google_referer.html")
                return response.text, 'google_referer'
                
        except Exception as e:
            logger.error(f"Google referer failed: {e}")
            
        return None, None
        
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
            
        # Remove commas and clean up
        clean_text = text.replace(',', '').replace(' ', '')
        
        # Look for patterns like $1,500,000 or 1500000
        price_match = re.search(r'[\$]?([0-9,]+)', clean_text)
        if price_match:
            try:
                return float(price_match.group(1).replace(',', ''))
            except ValueError:
                pass
                
        return None
        
    def extract_number(self, text):
        """Extract number from text"""
        if not text:
            return None
        number_match = re.search(r'(\d+)', text)
        if number_match:
            try:
                return int(number_match.group(1))
            except ValueError:
                pass
        return None
        
    def scrape_inmuebles24(self, urls):
        """Scrape Inmuebles24 listings"""
        logger.info("=== SCRAPING INMUEBLES24 ===")
        listings = []
        
        for url in urls:
            logger.info(f"Scraping Inmuebles24: {url}")
            html, method = self.test_url_access(url, f"inmuebles24_{len(listings)}")
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for listing cards - try multiple selectors
                selectors = [
                    '[data-qa="posting PROPERTY"]',
                    '.posting',
                    '.listing-card',
                    '[data-to-posting]',
                    '.ads-container .posting'
                ]
                
                cards = []
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        logger.info(f"Found {len(cards)} listings with selector: {selector}")
                        break
                
                if not cards:
                    logger.warning("No listing cards found, checking page structure...")
                    # Save a snippet to see what we got
                    with open(f"data/html/inmuebles24_debug_{len(listings)}.txt", 'w') as f:
                        f.write(str(soup)[:5000])
                    continue
                
                for card in cards[:20]:  # Limit for testing
                    try:
                        listing = self.extract_inmuebles24_listing(card)
                        if listing:
                            listings.append(listing)
                            logger.info(f"Extracted listing: {listing['title'][:50]}...")
                    except Exception as e:
                        logger.error(f"Error extracting listing: {e}")
                        continue
                        
            time.sleep(1)  # Be respectful
            
        return listings
        
    def extract_inmuebles24_listing(self, card):
        """Extract listing data from Inmuebles24 card"""
        listing = {
            'source': 'inmuebles24',
            'title': None,
            'price_mxn': None,
            'bedrooms': None,
            'bathrooms': None,
            'size_m2': None,
            'colonia': None,
            'description': None,
            'url': None,
            'images': []
        }
        
        # Title
        title_elem = card.find(['h2', 'h3', 'a']) or card.find(class_=lambda x: x and 'title' in x.lower())
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
            
        # URL
        link_elem = card.find('a', href=True)
        if link_elem:
            listing['url'] = urljoin('https://www.inmuebles24.com/', link_elem['href'])
            
        # Price
        price_elem = card.find(class_=lambda x: x and 'price' in x.lower()) or \
                    card.find(string=re.compile(r'\$[0-9,]+'))
        if price_elem:
            if hasattr(price_elem, 'get_text'):
                price_text = price_elem.get_text(strip=True)
            else:
                price_text = str(price_elem)
            listing['price_mxn'] = self.extract_price(price_text)
            
        # Property details (bedrooms, bathrooms, size)
        details = card.find_all(string=re.compile(r'(\d+\s*(rec|bed|dorm|hab|baño|bath|m²|m2))'))
        for detail in details:
            if 'rec' in detail.lower() or 'bed' in detail.lower() or 'dorm' in detail.lower() or 'hab' in detail.lower():
                listing['bedrooms'] = self.extract_number(detail)
            elif 'baño' in detail.lower() or 'bath' in detail.lower():
                listing['bathrooms'] = self.extract_number(detail)
            elif 'm²' in detail.lower() or 'm2' in detail.lower():
                listing['size_m2'] = self.extract_number(detail)
                
        # Location
        location_elem = card.find(class_=lambda x: x and ('location' in x.lower() or 'address' in x.lower()))
        if location_elem:
            listing['colonia'] = location_elem.get_text(strip=True)
            
        # Images
        img_elems = card.find_all('img', src=True)
        for img in img_elems:
            src = img['src']
            if 'placeholder' not in src and src.startswith('http'):
                listing['images'].append(src)
                
        return listing if listing['title'] else None
        
    def scrape_vivanuncios(self, urls):
        """Scrape VivaAnuncios listings"""
        logger.info("=== SCRAPING VIVANUNCIOS ===")
        listings = []
        
        for url in urls:
            logger.info(f"Scraping VivaAnuncios: {url}")
            html, method = self.test_url_access(url, f"vivanuncios_{len(listings)}")
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try multiple selectors for VivaAnuncios
                selectors = [
                    '.listing-card',
                    '.ad-card',
                    '[data-testid="ad-card"]',
                    '.result-item',
                    '.ads-list .ad'
                ]
                
                cards = []
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        logger.info(f"Found {len(cards)} listings with selector: {selector}")
                        break
                
                if not cards:
                    logger.warning("No listing cards found")
                    continue
                
                for card in cards[:20]:  # Limit for testing
                    try:
                        listing = self.extract_vivanuncios_listing(card)
                        if listing:
                            listings.append(listing)
                            logger.info(f"Extracted listing: {listing['title'][:50]}...")
                    except Exception as e:
                        logger.error(f"Error extracting listing: {e}")
                        continue
                        
            time.sleep(1)
            
        return listings
        
    def extract_vivanuncios_listing(self, card):
        """Extract listing data from VivaAnuncios card"""
        listing = {
            'source': 'vivanuncios',
            'title': None,
            'price_mxn': None,
            'bedrooms': None,
            'bathrooms': None,
            'size_m2': None,
            'colonia': None,
            'description': None,
            'url': None,
            'images': []
        }
        
        # Similar extraction logic as Inmuebles24
        # Title
        title_elem = card.find(['h2', 'h3', 'a']) or card.find(class_=lambda x: x and 'title' in x.lower())
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
            
        # URL
        link_elem = card.find('a', href=True)
        if link_elem:
            listing['url'] = urljoin('https://www.vivanuncios.com.mx/', link_elem['href'])
            
        # Price
        price_elem = card.find(class_=lambda x: x and 'price' in x.lower()) or \
                    card.find(string=re.compile(r'\$[0-9,]+'))
        if price_elem:
            if hasattr(price_elem, 'get_text'):
                price_text = price_elem.get_text(strip=True)
            else:
                price_text = str(price_elem)
            listing['price_mxn'] = self.extract_price(price_text)
            
        return listing if listing['title'] else None
        
    def scrape_century21(self, urls):
        """Scrape Century21 Mexico listings"""
        logger.info("=== SCRAPING CENTURY21 ===")
        listings = []
        
        for url in urls:
            logger.info(f"Scraping Century21: {url}")
            html, method = self.test_url_access(url, f"century21_{len(listings)}")
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try multiple selectors
                selectors = [
                    '.property-card',
                    '.listing-item',
                    '.result-item',
                    '[data-property-id]'
                ]
                
                cards = []
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        logger.info(f"Found {len(cards)} listings with selector: {selector}")
                        break
                
                if not cards:
                    logger.warning("No listing cards found")
                    continue
                
                for card in cards[:20]:
                    try:
                        listing = self.extract_century21_listing(card)
                        if listing:
                            listings.append(listing)
                            logger.info(f"Extracted listing: {listing['title'][:50]}...")
                    except Exception as e:
                        logger.error(f"Error extracting listing: {e}")
                        continue
                        
            time.sleep(1)
            
        return listings
        
    def extract_century21_listing(self, card):
        """Extract listing data from Century21 card"""
        listing = {
            'source': 'century21',
            'title': None,
            'price_mxn': None,
            'bedrooms': None,
            'bathrooms': None,
            'size_m2': None,
            'colonia': None,
            'description': None,
            'url': None,
            'images': []
        }
        
        # Similar extraction logic
        title_elem = card.find(['h2', 'h3', 'a']) or card.find(class_=lambda x: x and 'title' in x.lower())
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
            
        link_elem = card.find('a', href=True)
        if link_elem:
            listing['url'] = urljoin('https://www.century21mexico.com/', link_elem['href'])
            
        price_elem = card.find(class_=lambda x: x and 'price' in x.lower()) or \
                    card.find(string=re.compile(r'\$[0-9,]+'))
        if price_elem:
            if hasattr(price_elem, 'get_text'):
                price_text = price_elem.get_text(strip=True)
            else:
                price_text = str(price_elem)
            listing['price_mxn'] = self.extract_price(price_text)
            
        return listing if listing['title'] else None
        
    def store_listings(self, listings):
        """Store listings in database"""
        logger.info(f"Storing {len(listings)} listings in database...")
        
        # First, clear existing data
        logger.info("Clearing existing listings...")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM listings")
        conn.commit()
        conn.close()
        
        stored_count = 0
        for listing in listings:
            try:
                # Generate ID
                listing_id = hashlib.md5(f"{listing['source']}_{listing.get('url', '')}{listing.get('title', '')}".encode()).hexdigest()[:16]
                
                # Convert images list to JSON string
                images_json = json.dumps(listing.get('images', []))
                
                # Calculate price per m2
                price_per_m2 = None
                if listing.get('price_mxn') and listing.get('size_m2'):
                    price_per_m2 = listing['price_mxn'] / listing['size_m2']
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO listings (
                        id, source, url, title, price_mxn, bedrooms, bathrooms, size_m2,
                        city, colonia, description, images, price_per_m2, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    price_per_m2,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing listing {listing.get('title', 'Unknown')}: {e}")
                continue
                
        logger.info(f"Successfully stored {stored_count} listings")
        return stored_count
        
def main():
    """Main scraping function"""
    logger.info("Starting real estate scraping for CDMX...")
    
    scraper = RealEstateScraper()
    
    # URLs to scrape
    urls = {
        'inmuebles24': [
            'https://www.inmuebles24.com/departamentos-en-venta-en-ciudad-de-mexico.html',
            'https://www.inmuebles24.com/casas-en-venta-en-ciudad-de-mexico.html',
            'https://www.inmuebles24.com/terrenos-en-venta-en-ciudad-de-mexico.html'
        ],
        'vivanuncios': [
            'https://www.vivanuncios.com.mx/s-venta-inmuebles/ciudad-de-mexico/v1c1097l1014p1'
        ],
        'century21': [
            'https://www.century21mexico.com/resultados?operacion=venta&tipo=departamento&estado=ciudad-de-mexico'
        ]
    }
    
    all_listings = []
    
    # Scrape each site
    try:
        all_listings.extend(scraper.scrape_inmuebles24(urls['inmuebles24']))
    except Exception as e:
        logger.error(f"Failed to scrape Inmuebles24: {e}")
        
    try:
        all_listings.extend(scraper.scrape_vivanuncios(urls['vivanuncios']))
    except Exception as e:
        logger.error(f"Failed to scrape VivaAnuncios: {e}")
        
    try:
        all_listings.extend(scraper.scrape_century21(urls['century21']))
    except Exception as e:
        logger.error(f"Failed to scrape Century21: {e}")
        
    logger.info(f"Total listings scraped: {len(all_listings)}")
    
    if all_listings:
        stored = scraper.store_listings(all_listings)
        logger.info(f"Scraping complete! Stored {stored} real listings in database.")
        
        # Show sample of what we got
        for i, listing in enumerate(all_listings[:5]):
            logger.info(f"Sample {i+1}: {listing['title']} - ${listing.get('price_mxn', 'N/A')} - {listing.get('colonia', 'N/A')}")
    else:
        logger.warning("No listings were successfully scraped!")
        
if __name__ == '__main__':
    main()