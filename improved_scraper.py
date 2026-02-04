#!/usr/bin/env python3
"""Improved real estate scraper for CDMX - REAL DATA ONLY"""

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
from urllib.parse import urljoin, urlparse, quote, parse_qs
import gzip
import hashlib

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedRealEstateScraper:
    def __init__(self):
        self.db = PolpiDB()
        self.session = requests.Session()
        self.cloudscraper_session = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(self.headers)
        
    def safe_get(self, url, site_name="unknown"):
        """Safely get a URL with multiple fallback methods"""
        logger.info(f"Fetching {site_name}: {url}")
        
        methods = [
            ("regular_requests", self._get_regular),
            ("cloudscraper", self._get_cloudscraper),
            ("requests_with_referer", self._get_with_referer),
        ]
        
        for method_name, method_func in methods:
            try:
                response = method_func(url)
                if response and response.status_code == 200:
                    logger.info(f"Success with {method_name} - Status: {response.status_code}")
                    
                    # Handle gzipped content
                    content = self._decompress_response(response)
                    if content:
                        filename = f"{site_name}_{method_name}.html"
                        self.save_html(content, filename)
                        return content, method_name
                    else:
                        logger.warning(f"Failed to decompress response from {method_name}")
                else:
                    logger.warning(f"{method_name} failed with status: {response.status_code if response else 'No response'}")
            except Exception as e:
                logger.error(f"{method_name} failed with error: {e}")
                
        return None, None
    
    def _get_regular(self, url):
        return self.session.get(url, timeout=30)
    
    def _get_cloudscraper(self, url):
        return self.cloudscraper_session.get(url, timeout=30)
    
    def _get_with_referer(self, url):
        headers = self.headers.copy()
        headers['Referer'] = 'https://www.google.com/'
        return self.session.get(url, headers=headers, timeout=30)
    
    def _decompress_response(self, response):
        """Decompress response content if it's gzipped"""
        try:
            content = response.content
            
            # Check if content is gzipped
            if content.startswith(b'\x1f\x8b'):
                logger.info("Decompressing gzipped content...")
                content = gzip.decompress(content)
            
            # Try to decode as text
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return content.decode('latin-1')
                except UnicodeDecodeError:
                    logger.error("Could not decode response content")
                    return None
                    
        except Exception as e:
            logger.error(f"Error decompressing response: {e}")
            return response.text
            
    def save_html(self, content, filename):
        """Save HTML content to data/html directory"""
        filepath = f"data/html/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved HTML to {filepath}")
    
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
            
        # Remove commas and clean up
        clean_text = re.sub(r'[^\d.,]', '', text)
        
        # Look for patterns like $1,500,000 or 1500000
        price_match = re.search(r'([0-9,]+(?:\.[0-9]+)?)', clean_text)
        if price_match:
            try:
                price_str = price_match.group(1).replace(',', '')
                return float(price_str)
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
    
    def try_api_endpoints(self, base_url, search_params=None):
        """Try to find API endpoints for a site"""
        potential_apis = [
            f"{base_url}/api/search",
            f"{base_url}/api/properties",
            f"{base_url}/api/listings",
            f"{base_url}/search/api",
            f"{base_url}/properties/api",
        ]
        
        for api_url in potential_apis:
            try:
                logger.info(f"Trying API endpoint: {api_url}")
                response = self.session.get(api_url, params=search_params, timeout=15)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and isinstance(data, (dict, list)):
                            logger.info(f"Found working API at {api_url}")
                            return data, api_url
                    except:
                        pass
            except Exception as e:
                logger.debug(f"API endpoint {api_url} failed: {e}")
                continue
                
        return None, None
    
    def scrape_vivanuncios_new(self):
        """Scrape VivaAnuncios with improved approach"""
        logger.info("=== SCRAPING VIVANUNCIOS (IMPROVED) ===")
        listings = []
        
        base_url = "https://www.vivanuncios.com.mx"
        search_url = "https://www.vivanuncios.com.mx/s-venta-inmuebles/ciudad-de-mexico/v1c1097l1014p1"
        
        # Try API first
        api_data, api_url = self.try_api_endpoints(base_url, {
            'category': '1097',
            'location': '1014',
            'operation': 'venta'
        })
        
        if api_data:
            logger.info(f"Using API data from {api_url}")
            # Process API data here
            return self.process_vivanuncios_api(api_data)
        
        # Fallback to HTML scraping
        html, method = self.safe_get(search_url, "vivanuncios")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # More comprehensive selectors for VivaAnuncios
            selectors = [
                '.tileV1',  # Common VivaAnuncios listing class
                '[data-testid="listing-card"]',
                '.listing-item',
                '.ad-card',
                '.result-item',
                'article[data-ad-id]',
                '.ads-container > div',
                '.search-results > div',
                '.listing',
                '[class*="listing"]'
            ]
            
            cards = []
            for selector in selectors:
                cards = soup.select(selector)
                if cards:
                    logger.info(f"Found {len(cards)} listings with selector: {selector}")
                    break
            
            if not cards:
                logger.warning("No listing cards found. Saving page structure for analysis...")
                # Save a debug file with page structure
                with open('data/html/vivanuncios_debug_structure.html', 'w', encoding='utf-8') as f:
                    # Extract potential listing containers
                    divs_with_classes = soup.find_all('div', class_=True)
                    f.write(f"Found {len(divs_with_classes)} divs with classes:\n")
                    for div in divs_with_classes[:50]:  # Limit to first 50
                        f.write(f"<div class=\"{' '.join(div.get('class', []))}\">\n")
                        f.write(div.get_text()[:200] + "...\n</div>\n\n")
                return []
                
            for card in cards[:20]:  # Limit for testing
                try:
                    listing = self.extract_vivanuncios_listing(card)
                    if listing:
                        listings.append(listing)
                        logger.info(f"Extracted listing: {listing['title'][:50]}...")
                except Exception as e:
                    logger.error(f"Error extracting listing: {e}")
                    continue
        
        return listings
    
    def process_vivanuncios_api(self, api_data):
        """Process VivaAnuncios API data"""
        listings = []
        # This would depend on the actual API structure
        # For now, return empty since we need to inspect the actual API response
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
        
        # Title - try multiple approaches
        title_selectors = ['h2', 'h3', 'h4', '[class*="title"]', 'a[title]', '.listing-title']
        for selector in title_selectors:
            title_elem = card.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True) or title_elem.get('title', '')
                if title_text and len(title_text) > 10:  # Reasonable title length
                    listing['title'] = title_text
                    break
        
        # URL
        link_elem = card.find('a', href=True)
        if link_elem:
            href = link_elem['href']
            if href.startswith('/'):
                listing['url'] = urljoin('https://www.vivanuncios.com.mx', href)
            elif href.startswith('http'):
                listing['url'] = href
        
        # Price - look for money symbols and numbers
        price_text = card.get_text()
        price_matches = re.findall(r'\$\s*([0-9,]+(?:\.[0-9]+)?)', price_text)
        if price_matches:
            for price_match in price_matches:
                price = self.extract_price('$' + price_match)
                if price and price > 10000:  # Reasonable minimum price
                    listing['price_mxn'] = price
                    break
        
        # Property details
        text_content = card.get_text()
        
        # Bedrooms
        bed_patterns = [r'(\d+)\s*rec[aáá]mar[ae]s?', r'(\d+)\s*habitaci[oó]n[se]*', r'(\d+)\s*bed']
        for pattern in bed_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                listing['bedrooms'] = int(match.group(1))
                break
        
        # Bathrooms
        bath_patterns = [r'(\d+)\s*ba[ñn]os?', r'(\d+)\s*bathroom']
        for pattern in bath_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                listing['bathrooms'] = int(match.group(1))
                break
        
        # Size
        size_patterns = [r'(\d+)\s*m[²2]', r'(\d+)\s*metros']
        for pattern in size_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                listing['size_m2'] = int(match.group(1))
                break
        
        # Location - try to extract neighborhood/colonia
        location_elem = card.select_one('[class*="location"], [class*="address"], [class*="zona"]')
        if location_elem:
            listing['colonia'] = location_elem.get_text(strip=True)
        
        # Images
        img_elems = card.find_all('img', src=True)
        for img in img_elems:
            src = img['src']
            if 'placeholder' not in src.lower() and src.startswith('http'):
                listing['images'].append(src)
        
        return listing if listing['title'] else None
    
    def try_inmuebles24_alternative(self):
        """Try alternative approaches for Inmuebles24"""
        logger.info("=== TRYING ALTERNATIVE APPROACHES FOR INMUEBLES24 ===")
        
        # Try searching for specific neighborhoods first
        neighborhoods = ['roma-norte', 'condesa', 'polanco', 'centro', 'del-valle']
        listings = []
        
        for neighborhood in neighborhoods:
            try:
                # Try more specific URLs
                url = f"https://www.inmuebles24.com/departamentos-en-venta-en-{neighborhood}-ciudad-de-mexico.html"
                html, method = self.safe_get(url, f"inmuebles24_{neighborhood}")
                
                if html and "403" not in html:
                    soup = BeautifulSoup(html, 'html.parser')
                    # Look for any data
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'posting' in script.string.lower():
                            logger.info(f"Found potential data in {neighborhood}")
                            # Could contain JSON data
                            try:
                                # Extract JSON if present
                                json_match = re.search(r'\{.*"posting".*\}', script.string)
                                if json_match:
                                    logger.info("Found JSON data in script tag")
                            except:
                                pass
                time.sleep(2)  # Be respectful
            except Exception as e:
                logger.error(f"Failed to scrape {neighborhood}: {e}")
        
        return listings
    
    def scrape_century21_improved(self):
        """Improved Century21 scraper"""
        logger.info("=== SCRAPING CENTURY21 (IMPROVED) ===")
        listings = []
        
        # Try multiple search URLs
        urls = [
            "https://www.century21mexico.com/resultados?operacion=venta&tipo=departamento&estado=ciudad-de-mexico",
            "https://www.century21mexico.com/resultados?operacion=venta&tipo=casa&estado=ciudad-de-mexico",
            "https://www.century21mexico.com/api/search?operacion=venta&estado=ciudad-de-mexico&tipo=departamento",
            "https://www.century21mexico.com/search?q=ciudad%20de%20mexico&operacion=venta"
        ]
        
        for url in urls:
            try:
                html, method = self.safe_get(url, f"century21_attempt_{len(listings)}")
                
                if html:
                    # Check if it's JSON
                    if url.endswith('.json') or '/api/' in url:
                        try:
                            data = json.loads(html)
                            logger.info(f"Got JSON data from {url}")
                            # Process JSON data
                            continue
                        except:
                            pass
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for property listings or AJAX endpoints in the page
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string:
                            # Look for AJAX URLs or data
                            ajax_urls = re.findall(r'url\s*:\s*["\']([^"\']*(?:search|result|propert|api)[^"\']*)["\']', script.string)
                            for ajax_url in ajax_urls:
                                logger.info(f"Found potential AJAX endpoint: {ajax_url}")
                                try:
                                    if ajax_url.startswith('/'):
                                        ajax_url = 'https://www.century21mexico.com' + ajax_url
                                    ajax_response = self.session.get(ajax_url, timeout=15)
                                    if ajax_response.status_code == 200:
                                        try:
                                            ajax_data = ajax_response.json()
                                            if ajax_data:
                                                logger.info(f"Got data from AJAX endpoint: {ajax_url}")
                                                # Process the AJAX data
                                        except:
                                            pass
                                except Exception as e:
                                    logger.debug(f"AJAX call failed: {e}")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error with Century21 URL {url}: {e}")
        
        return listings
    
    def store_listings(self, listings):
        """Store listings in database"""
        logger.info(f"Storing {len(listings)} listings in database...")
        
        if not listings:
            logger.warning("No listings to store!")
            return 0
        
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
                # Generate unique ID
                id_string = f"{listing['source']}_{listing.get('url', '')}{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Convert images list to JSON string
                images_json = json.dumps(listing.get('images', []))
                
                # Calculate price per m2
                price_per_m2 = None
                if listing.get('price_mxn') and listing.get('size_m2') and listing['size_m2'] > 0:
                    price_per_m2 = listing['price_mxn'] / listing['size_m2']
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
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
                logger.error(f"Error storing listing '{listing.get('title', 'Unknown')}': {e}")
                continue
                
        logger.info(f"Successfully stored {stored_count} listings")
        return stored_count

def main():
    """Main scraping function"""
    logger.info("Starting improved real estate scraping for CDMX...")
    
    scraper = ImprovedRealEstateScraper()
    
    all_listings = []
    
    # Try VivaAnuncios first (most likely to work)
    try:
        vivanuncios_listings = scraper.scrape_vivanuncios_new()
        all_listings.extend(vivanuncios_listings)
        logger.info(f"VivaAnuncios: {len(vivanuncios_listings)} listings")
    except Exception as e:
        logger.error(f"Failed to scrape VivaAnuncios: {e}")
    
    # Try Century21
    try:
        century21_listings = scraper.scrape_century21_improved()
        all_listings.extend(century21_listings)
        logger.info(f"Century21: {len(century21_listings)} listings")
    except Exception as e:
        logger.error(f"Failed to scrape Century21: {e}")
    
    # Try Inmuebles24 alternatives
    try:
        inmuebles24_listings = scraper.try_inmuebles24_alternative()
        all_listings.extend(inmuebles24_listings)
        logger.info(f"Inmuebles24: {len(inmuebles24_listings)} listings")
    except Exception as e:
        logger.error(f"Failed to scrape Inmuebles24: {e}")
    
    logger.info(f"Total listings scraped: {len(all_listings)}")
    
    if all_listings:
        stored = scraper.store_listings(all_listings)
        logger.info(f"SUCCESS: Stored {stored} real listings in database!")
        
        # Show samples
        for i, listing in enumerate(all_listings[:5]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
            logger.info(f"Sample {i+1}: {listing['title'][:60]} - {price_str} - {listing.get('colonia', 'N/A')}")
    else:
        logger.error("FAILED: No listings were successfully scraped!")
        logger.info("Next steps:")
        logger.info("1. Check the saved HTML files in data/html/ to see what the sites actually returned")
        logger.info("2. The sites might need browser automation instead of simple HTTP requests")
        logger.info("3. Consider using Selenium or Playwright for JavaScript-heavy sites")

if __name__ == '__main__':
    main()