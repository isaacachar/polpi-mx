#!/usr/bin/env python3
"""RE/MAX Mexico scraper - extracts high-quality CDMX listings using Selenium"""

import sys
import json
import time
import re
import hashlib
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add project root to path
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class RemaxScraper:
    def __init__(self, headless=True):
        self.db = PolpiDB()
        self.headless = headless
        self.driver = None
        self.base_url = 'https://remax.com.mx/propiedades'
        self.inserted_count = 0
        self.error_count = 0
        
    def init_driver(self):
        """Initialize Chrome webdriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def get_search_urls(self):
        """Generate search URLs for CDMX sales and rentals"""
        urls = []
        
        # Sales - CDMX
        base_sale = f"{self.base_url}/ciudad+de+mexico_ciudad+de+mexico/venta"
        urls.append(base_sale)
        # Add pagination (RE/MAX seems to have pages)
        for page in range(2, 11):  # Pages 2-10
            urls.append(f"{base_sale}?pagina={page}")
        
        # Rentals - CDMX
        base_rent = f"{self.base_url}/ciudad+de+mexico_ciudad+de+mexico/renta"
        urls.append(base_rent)
        for page in range(2, 6):  # Pages 2-5 for rentals
            urls.append(f"{base_rent}?pagina={page}")
        
        return urls
    
    def extract_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and spaces
        price_text = price_text.replace('$', '').replace(',', '').replace(' ', '')
        
        # Extract numbers
        match = re.search(r'([\d\.]+)', price_text)
        if match:
            try:
                price = float(match.group(1))
                # Handle millions (M) or thousands (K)
                if 'M' in price_text.upper() or 'MILLÓN' in price_text.upper():
                    price = price * 1_000_000
                elif 'K' in price_text.upper() or 'MIL' in price_text.upper():
                    price = price * 1_000
                return price
            except:
                return None
        return None
    
    def extract_number(self, text):
        """Extract first number from text"""
        if not text:
            return None
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else None
    
    def scrape_listing_page(self, listing_url):
        """Scrape detailed information from a single listing page"""
        try:
            print(f"  → Scraping details: {listing_url}")
            self.driver.get(listing_url)
            time.sleep(2)  # Wait for page to load
            
            listing_data = {
                'source': 'remax',
                'url': listing_url,
                'source_id': listing_url.split('/')[-1] if '/' in listing_url else None,
            }
            
            # Extract title
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1.property-title, h1')
                listing_data['title'] = title_elem.text.strip()
            except NoSuchElementException:
                listing_data['title'] = 'RE/MAX Property'
            
            # Extract price
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, '.property-price, .price, [class*="price"]')
                listing_data['price_mxn'] = self.extract_price(price_elem.text)
            except NoSuchElementException:
                pass
            
            # Extract property details
            try:
                # Look for details section with bedrooms, bathrooms, size
                details = self.driver.find_elements(By.CSS_SELECTOR, '.property-details li, .details-list li, [class*="detail"]')
                
                for detail in details:
                    text = detail.text.lower()
                    
                    if 'recámar' in text or 'habitacion' in text or 'bedroom' in text:
                        listing_data['bedrooms'] = self.extract_number(detail.text)
                    elif 'baño' in text or 'bathroom' in text:
                        listing_data['bathrooms'] = self.extract_number(detail.text)
                    elif 'm²' in text or 'metros' in text or 'sqm' in text:
                        size = self.extract_number(detail.text)
                        if size and not listing_data.get('size_m2'):
                            listing_data['size_m2'] = size
                    elif 'terreno' in text or 'lote' in text:
                        listing_data['lot_size_m2'] = self.extract_number(detail.text)
                    elif 'estacionamiento' in text or 'parking' in text:
                        listing_data['parking_spaces'] = self.extract_number(detail.text)
            except Exception as e:
                print(f"    ⚠ Error extracting details: {e}")
            
            # Extract location
            try:
                location_elem = self.driver.find_element(By.CSS_SELECTOR, '.property-location, .location, [class*="location"]')
                location_text = location_elem.text
                
                # Parse location (usually "Colonia, Ciudad")
                parts = [p.strip() for p in location_text.split(',')]
                if len(parts) >= 2:
                    listing_data['colonia'] = parts[0]
                    listing_data['city'] = parts[1] if 'ciudad de méxico' in parts[1].lower() or 'cdmx' in parts[1].lower() else 'Ciudad de México'
                elif len(parts) == 1:
                    listing_data['colonia'] = parts[0]
                    listing_data['city'] = 'Ciudad de México'
            except NoSuchElementException:
                listing_data['city'] = 'Ciudad de México'
            
            # Extract description
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, '.property-description, .description, [class*="description"]')
                listing_data['description'] = desc_elem.text.strip()[:1000]  # Limit to 1000 chars
            except NoSuchElementException:
                pass
            
            # Extract agent info
            try:
                agent_name_elem = self.driver.find_element(By.CSS_SELECTOR, '.agent-name, .agente, [class*="agent"]')
                listing_data['agent_name'] = agent_name_elem.text.strip()
            except NoSuchElementException:
                pass
            
            try:
                agent_phone_elem = self.driver.find_element(By.CSS_SELECTOR, '.agent-phone, [class*="telefono"], [class*="phone"]')
                listing_data['agent_phone'] = agent_phone_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract property type from URL or title
            url_lower = listing_url.lower()
            title_lower = listing_data.get('title', '').lower()
            
            if 'departamento' in url_lower or 'departamento' in title_lower or 'apartment' in title_lower:
                listing_data['property_type'] = 'departamento'
            elif 'casa' in url_lower or 'casa' in title_lower or 'house' in title_lower:
                listing_data['property_type'] = 'casa'
            elif 'terreno' in url_lower or 'terreno' in title_lower or 'land' in title_lower:
                listing_data['property_type'] = 'terreno'
            else:
                listing_data['property_type'] = 'otro'
            
            # Determine listing type from URL
            listing_data['listing_type'] = 'rental' if 'renta' in listing_url else 'sale'
            
            # Extract HIGH-QUALITY IMAGES (priority!)
            images = []
            try:
                # Try multiple selectors for image galleries
                image_selectors = [
                    'img[class*="gallery"]',
                    'img[class*="property-image"]',
                    '.property-photos img',
                    '[class*="gallery"] img',
                    '[class*="carousel"] img',
                    '.slider img',
                    'img[src*="remax"]',
                ]
                
                for selector in image_selectors:
                    try:
                        img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            src = img.get_attribute('src') or img.get_attribute('data-src')
                            if src and 'http' in src and src not in images:
                                # Prefer large/original images
                                if 'thumb' not in src.lower() and 'small' not in src.lower():
                                    images.append(src)
                        
                        if images:
                            break  # Found images, stop trying
                    except:
                        continue
                
                # Limit to first 20 images
                listing_data['images'] = images[:20]
                print(f"    ✓ Found {len(images)} images")
                
            except Exception as e:
                print(f"    ⚠ Error extracting images: {e}")
                listing_data['images'] = []
            
            # Try to extract coordinates from map if available
            try:
                # Look for map data or script with coordinates
                scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    
                    # Look for lat/lng patterns
                    lat_match = re.search(r'lat["\']?\s*:\s*([0-9\.-]+)', script_text)
                    lng_match = re.search(r'lng["\']?\s*:\s*([0-9\.-]+)', script_text)
                    
                    if lat_match and lng_match:
                        listing_data['lat'] = float(lat_match.group(1))
                        listing_data['lng'] = float(lng_match.group(1))
                        break
            except Exception as e:
                print(f"    ⚠ Could not extract coordinates: {e}")
            
            return listing_data
            
        except Exception as e:
            print(f"    ✗ Error scraping listing page: {e}")
            return None
    
    def scrape_search_page(self, url):
        """Scrape listing links from a search results page"""
        try:
            print(f"\n📄 Scraping search page: {url}")
            self.driver.get(url)
            
            # Wait and scroll to trigger lazy loading
            time.sleep(5)  # Initial wait for page load
            
            # Scroll down to load more content
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Extract all listing links - RE/MAX uses cards with data attributes or onclick handlers
            listing_links = set()
            
            # Method 1: Try to find direct property links
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/propiedades/"]')
                for link in links:
                    href = link.get_attribute('href')
                    # Look for individual property pages (have specific ID or details)
                    if href and 'remax.com.mx' in href and href.count('/') >= 5:  # Individual properties have longer URLs
                        listing_links.add(href)
            except:
                pass
            
            # Method 2: Look for cards with onclick or data attributes
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, '.card, [class*="property"], [class*="listing"]')
                for card in cards:
                    # Try to find links within cards
                    try:
                        card_links = card.find_elements(By.TAG_NAME, 'a')
                        for link in card_links:
                            href = link.get_attribute('href')
                            if href and 'propiedad' in href:
                                listing_links.add(href)
                    except:
                        pass
                    
                    # Check onclick attributes
                    onclick = card.get_attribute('onclick')
                    if onclick and 'propiedad' in onclick:
                        # Extract URL from onclick
                        match = re.search(r'["\']([^"\']*propiedad[^"\']*)["\']', onclick)
                        if match:
                            url_part = match.group(1)
                            if not url_part.startswith('http'):
                                url_part = 'https://remax.com.mx' + url_part
                            listing_links.add(url_part)
            except:
                pass
            
            # Method 3: Check for JSON data in scripts
            try:
                scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    script_content = script.get_attribute('innerHTML') or ''
                    # Look for property URLs in JSON
                    urls = re.findall(r'https://remax\.com\.mx/propiedades/[^"\s]+', script_content)
                    listing_links.update(urls)
            except:
                pass
            
            print(f"  ✓ Found {len(listing_links)} unique listings on this page")
            
            # If we didn't find any, save debug info
            if not listing_links:
                debug_file = f'/Users/isaachomefolder/Desktop/polpi-mx/remax_debug_{int(time.time())}.html'
                with open(debug_file, 'w') as f:
                    f.write(self.driver.page_source)
                print(f"  ⚠ No listings found - saved debug HTML to {debug_file}")
            
            return list(listing_links)
            
        except Exception as e:
            print(f"  ✗ Error scraping search page: {e}")
            return []
    
    def scrape(self):
        """Main scraping method"""
        print("=" * 60)
        print("RE/MAX Mexico Scraper - High-Quality CDMX Listings")
        print("=" * 60)
        
        try:
            self.init_driver()
            
            # Get all search URLs
            search_urls = self.get_search_urls()
            print(f"\n📋 Total search pages to scrape: {len(search_urls)}")
            
            all_listing_urls = set()
            
            # Step 1: Collect all listing URLs from search pages
            for search_url in search_urls:
                listing_urls = self.scrape_search_page(search_url)
                all_listing_urls.update(listing_urls)
                time.sleep(3)  # Respectful delay between search pages
            
            print(f"\n📊 Total unique listings found: {len(all_listing_urls)}")
            
            # Step 2: Scrape each listing detail page
            for i, listing_url in enumerate(all_listing_urls, 1):
                print(f"\n[{i}/{len(all_listing_urls)}] Processing listing...")
                
                try:
                    listing_data = self.scrape_listing_page(listing_url)
                    
                    if listing_data and listing_data.get('title'):
                        # Validate minimum data quality
                        if not listing_data.get('price_mxn'):
                            print(f"    ⚠ Skipping: No price")
                            self.error_count += 1
                            continue
                        
                        if not listing_data.get('images'):
                            print(f"    ⚠ Warning: No images found (still saving)")
                        
                        # Insert into database
                        try:
                            listing_id = self.db.insert_listing(listing_data)
                            self.inserted_count += 1
                            print(f"    ✓ Saved to DB (ID: {listing_id[:8]}...) - {len(listing_data.get('images', []))} images")
                        except Exception as e:
                            print(f"    ✗ Database error: {e}")
                            self.error_count += 1
                    else:
                        print(f"    ⚠ Skipping: Insufficient data")
                        self.error_count += 1
                    
                    # Respectful delay between listings
                    time.sleep(2.5)
                    
                except Exception as e:
                    print(f"    ✗ Error processing listing: {e}")
                    self.error_count += 1
                    continue
            
            # Print summary
            print("\n" + "=" * 60)
            print("SCRAPING COMPLETE")
            print("=" * 60)
            print(f"✓ Successfully inserted: {self.inserted_count} listings")
            print(f"✗ Errors/Skipped: {self.error_count}")
            print(f"📸 Focus: High-quality professional images")
            print("=" * 60)
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    scraper = RemaxScraper(headless=True)
    scraper.scrape()

if __name__ == '__main__':
    main()
