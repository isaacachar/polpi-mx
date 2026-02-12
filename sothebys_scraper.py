#!/usr/bin/env python3
"""Sotheby's International Realty Mexico scraper - extracts luxury CDMX listings"""

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

class SothebyScraper:
    def __init__(self, headless=True):
        self.db = PolpiDB()
        self.headless = headless
        self.driver = None
        self.base_url = 'https://www.sothebysrealty.com'
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
        """Generate search URLs for Mexico City luxury listings"""
        urls = []
        
        # Main Mexico City search - Sales (correct URL format with cm)
        base_sale = f"{self.base_url}/eng/sales/mexico-city-cm-mex"
        urls.append(base_sale)
        
        # Alternative CDMX URLs
        urls.append(f"{self.base_url}/eng/sales/cm-mex")  # Ciudad de Mexico state
        urls.append(f"{self.base_url}/eng/sales/mex")  # All Mexico
        
        # Try pagination if available
        for page in range(2, 4):
            urls.append(f"{base_sale}?page={page}")
        
        # Check for rentals
        urls.append(f"{self.base_url}/eng/rentals/mexico-city-cm-mex")
        
        return urls
    
    def extract_price(self, price_text):
        """Extract numeric price from text (USD or MXN)"""
        if not price_text:
            return None, None
        
        # Detect currency
        is_usd = '$' in price_text and 'USD' in price_text.upper() or 'US$' in price_text
        is_mxn = 'MXN' in price_text.upper() or '$' in price_text and not is_usd
        
        # Remove currency symbols and spaces
        price_text = price_text.replace('$', '').replace(',', '').replace(' ', '')
        price_text = re.sub(r'USD|MXN|US', '', price_text, flags=re.IGNORECASE)
        
        # Extract numbers
        match = re.search(r'([\d\.]+)', price_text)
        if match:
            try:
                price = float(match.group(1))
                
                # Handle millions (M) or thousands (K)
                if 'M' in price_text.upper() or 'MILL' in price_text.upper():
                    price = price * 1_000_000
                elif 'K' in price_text.upper():
                    price = price * 1_000
                
                # Convert to MXN if needed (approximate rate: 1 USD = 17 MXN)
                if is_usd:
                    return price * 17, price  # Return both MXN and USD
                else:
                    return price, None  # MXN only
            except:
                return None, None
        return None, None
    
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
            time.sleep(2.5)  # Wait for luxury site to load fully
            
            listing_data = {
                'source': 'sothebys',
                'url': listing_url,
                'source_id': listing_url.split('/')[-1].split('-')[-1] if '/' in listing_url else None,
            }
            
            # Extract title
            try:
                title_selectors = [
                    'h1[class*="property-title"]',
                    'h1[class*="title"]',
                    'h1.listing-title',
                    'h1',
                ]
                
                for selector in title_selectors:
                    try:
                        title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        listing_data['title'] = title_elem.text.strip()
                        break
                    except:
                        continue
                
                if not listing_data.get('title'):
                    listing_data['title'] = "Sotheby's Luxury Property"
            except:
                listing_data['title'] = "Sotheby's Luxury Property"
            
            # Extract price
            try:
                price_selectors = [
                    '[class*="property-price"]',
                    '[class*="price"]',
                    '.listing-price',
                    'span[class*="price"]',
                ]
                
                for selector in price_selectors:
                    try:
                        price_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        price_mxn, price_usd = self.extract_price(price_elem.text)
                        if price_mxn:
                            listing_data['price_mxn'] = price_mxn
                            if price_usd:
                                listing_data['price_usd'] = price_usd
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract property details (beds, baths, size)
            try:
                detail_selectors = [
                    '.property-features li',
                    '.property-details li',
                    '[class*="feature"] li',
                    '[class*="detail"]',
                ]
                
                details = []
                for selector in detail_selectors:
                    try:
                        details = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if details:
                            break
                    except:
                        continue
                
                for detail in details:
                    text = detail.text.lower()
                    
                    if 'bed' in text or 'recámar' in text or 'habitacion' in text:
                        listing_data['bedrooms'] = self.extract_number(detail.text)
                    elif 'bath' in text or 'baño' in text:
                        listing_data['bathrooms'] = self.extract_number(detail.text)
                    elif 'sq' in text or 'm²' in text or 'sqm' in text or 'metros' in text:
                        size = self.extract_number(detail.text)
                        if size:
                            # Check if it's square feet (convert to m²)
                            if 'sq ft' in text or 'sqft' in text:
                                listing_data['size_m2'] = int(size * 0.092903)  # Convert sq ft to m²
                            else:
                                listing_data['size_m2'] = size
                    elif 'lot' in text or 'terreno' in text or 'land' in text:
                        lot_size = self.extract_number(detail.text)
                        if lot_size and 'sq ft' in text:
                            listing_data['lot_size_m2'] = int(lot_size * 0.092903)
                        else:
                            listing_data['lot_size_m2'] = lot_size
                    elif 'parking' in text or 'garage' in text or 'estacionamiento' in text:
                        listing_data['parking_spaces'] = self.extract_number(detail.text)
            except Exception as e:
                print(f"    ⚠ Error extracting details: {e}")
            
            # Extract location
            try:
                location_selectors = [
                    '[class*="property-address"]',
                    '[class*="location"]',
                    '.listing-address',
                    'address',
                ]
                
                for selector in location_selectors:
                    try:
                        location_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        location_text = location_elem.text
                        
                        # Parse location
                        # Usually format: "Neighborhood, Mexico City, Mexico"
                        parts = [p.strip() for p in location_text.split(',')]
                        
                        if len(parts) >= 1:
                            listing_data['colonia'] = parts[0]
                        
                        # Check if Mexico City is mentioned
                        if any('mexico city' in p.lower() or 'ciudad de méxico' in p.lower() for p in parts):
                            listing_data['city'] = 'Ciudad de México'
                        else:
                            listing_data['city'] = 'Ciudad de México'  # Default for this scraper
                        
                        break
                    except:
                        continue
                
                if not listing_data.get('city'):
                    listing_data['city'] = 'Ciudad de México'
            except:
                listing_data['city'] = 'Ciudad de México'
            
            # Extract description
            try:
                desc_selectors = [
                    '[class*="property-description"]',
                    '[class*="description"]',
                    '.listing-description',
                    '[class*="remarks"]',
                ]
                
                for selector in desc_selectors:
                    try:
                        desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        listing_data['description'] = desc_elem.text.strip()[:1500]  # Luxury listings have longer descriptions
                        break
                    except:
                        continue
            except:
                pass
            
            # Extract agent info
            try:
                agent_selectors = [
                    '[class*="agent-name"]',
                    '[class*="broker-name"]',
                    '.listing-agent',
                ]
                
                for selector in agent_selectors:
                    try:
                        agent_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        listing_data['agent_name'] = agent_elem.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            try:
                phone_selectors = [
                    '[class*="agent-phone"]',
                    '[class*="phone"]',
                    'a[href^="tel:"]',
                ]
                
                for selector in phone_selectors:
                    try:
                        phone_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        listing_data['agent_phone'] = phone_elem.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Determine property type
            url_lower = listing_url.lower()
            title_lower = listing_data.get('title', '').lower()
            desc_lower = listing_data.get('description', '').lower()
            
            # Sotheby's usually has houses/villas/penthouses
            if 'condo' in title_lower or 'apartment' in title_lower or 'penthouse' in title_lower or 'departamento' in title_lower:
                listing_data['property_type'] = 'departamento'
            elif 'land' in title_lower or 'lot' in title_lower or 'terreno' in title_lower:
                listing_data['property_type'] = 'terreno'
            else:
                listing_data['property_type'] = 'casa'  # Default for luxury properties
            
            # Listing type (almost always sales for Sotheby's)
            listing_data['listing_type'] = 'rental' if 'rental' in url_lower else 'sale'
            
            # Extract HIGH-QUALITY LUXURY IMAGES (top priority!)
            images = []
            try:
                # Sotheby's typically has high-quality image galleries
                image_selectors = [
                    'img[class*="gallery"]',
                    'img[class*="property-photo"]',
                    'img[class*="listing-photo"]',
                    '[class*="photo-gallery"] img',
                    '[class*="image-gallery"] img',
                    '[class*="slider"] img',
                    'picture img',
                    'img[src*="sothebysrealty"]',
                ]
                
                for selector in image_selectors:
                    try:
                        img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            # Try multiple attributes
                            src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-lazy-src')
                            
                            if src and 'http' in src and src not in images:
                                # Filter out tiny images and icons
                                if 'thumb' not in src.lower() and 'icon' not in src.lower() and 'logo' not in src.lower():
                                    # Try to get high-res version
                                    src = src.replace('_small', '_large').replace('_medium', '_large')
                                    src = src.replace('/small/', '/large/').replace('/medium/', '/large/')
                                    images.append(src)
                        
                        if images:
                            break  # Found images
                    except:
                        continue
                
                # Also check for data in scripts (some sites load images via JS)
                if not images:
                    try:
                        scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                        for script in scripts:
                            script_text = script.get_attribute('innerHTML') or ''
                            # Look for image URLs in JSON data
                            urls = re.findall(r'https?://[^"\s]+\.(?:jpg|jpeg|png|webp)', script_text)
                            for url in urls:
                                if 'sotheby' in url and url not in images:
                                    images.append(url)
                    except:
                        pass
                
                listing_data['images'] = images[:25]  # More images for luxury properties
                print(f"    ✓ Found {len(images)} high-quality images")
                
            except Exception as e:
                print(f"    ⚠ Error extracting images: {e}")
                listing_data['images'] = []
            
            # Extract coordinates
            try:
                # Look for map data in scripts
                scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    script_text = script.get_attribute('innerHTML') or ''
                    
                    # Multiple coordinate patterns
                    patterns = [
                        (r'latitude["\']?\s*:\s*([0-9\.-]+)', r'longitude["\']?\s*:\s*([0-9\.-]+)'),
                        (r'lat["\']?\s*:\s*([0-9\.-]+)', r'lng["\']?\s*:\s*([0-9\.-]+)'),
                        (r'"lat":\s*([0-9\.-]+)', r'"lng":\s*([0-9\.-]+)'),
                    ]
                    
                    for lat_pattern, lng_pattern in patterns:
                        lat_match = re.search(lat_pattern, script_text)
                        lng_match = re.search(lng_pattern, script_text)
                        
                        if lat_match and lng_match:
                            listing_data['lat'] = float(lat_match.group(1))
                            listing_data['lng'] = float(lng_match.group(1))
                            break
                    
                    if listing_data.get('lat'):
                        break
            except Exception as e:
                print(f"    ⚠ Could not extract coordinates: {e}")
            
            # Extract amenities (luxury properties have many)
            amenities = []
            try:
                amenity_selectors = [
                    '[class*="amenities"] li',
                    '[class*="features"] li',
                    '[class*="property-features"] li',
                ]
                
                for selector in amenity_selectors:
                    try:
                        amenity_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in amenity_elements:
                            text = elem.text.strip()
                            if text and len(text) < 100:  # Reasonable amenity length
                                amenities.append(text)
                        
                        if amenities:
                            break
                    except:
                        continue
                
                if amenities:
                    listing_data['amenities'] = amenities[:30]  # Limit to 30 amenities
            except:
                pass
            
            return listing_data
            
        except Exception as e:
            print(f"    ✗ Error scraping listing page: {e}")
            return None
    
    def scrape_search_page(self, url):
        """Scrape listing links from a search results page"""
        try:
            print(f"\n📄 Scraping search page: {url}")
            self.driver.get(url)
            
            # Wait for listings to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/property/"], a[href*="/listing/"], [class*="property-card"] a'))
                )
            except TimeoutException:
                print("  ⚠ Timeout waiting for listings to load")
                return []
            
            time.sleep(3)  # Extra time for luxury site JS
            
            # Extract all listing links
            listing_links = set()
            
            # Try multiple selectors
            link_selectors = [
                'a[href*="/property/"]',
                'a[href*="/listing/"]',
                '[class*="property-card"] a',
                '[class*="listing-card"] a',
                '[class*="property-result"] a',
            ]
            
            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and ('property' in href or 'listing' in href) and 'sothebysrealty.com' in href:
                            listing_links.add(href)
                except:
                    continue
            
            print(f"  ✓ Found {len(listing_links)} unique luxury listings on this page")
            return list(listing_links)
            
        except Exception as e:
            print(f"  ✗ Error scraping search page: {e}")
            return []
    
    def scrape(self):
        """Main scraping method"""
        print("=" * 60)
        print("Sotheby's International Realty Mexico Scraper")
        print("LUXURY CDMX Properties - Premium Images")
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
                time.sleep(3)  # Respectful delay
            
            print(f"\n📊 Total unique luxury listings found: {len(all_listing_urls)}")
            
            # Step 2: Scrape each listing detail page
            for i, listing_url in enumerate(all_listing_urls, 1):
                print(f"\n[{i}/{len(all_listing_urls)}] Processing luxury listing...")
                
                try:
                    listing_data = self.scrape_listing_page(listing_url)
                    
                    if listing_data and listing_data.get('title'):
                        # Validate minimum data
                        if not listing_data.get('price_mxn') and not listing_data.get('price_usd'):
                            print(f"    ⚠ Skipping: No price")
                            self.error_count += 1
                            continue
                        
                        if not listing_data.get('images'):
                            print(f"    ⚠ Warning: No images found (unusual for Sotheby's)")
                        
                        # Insert into database
                        try:
                            listing_id = self.db.insert_listing(listing_data)
                            self.inserted_count += 1
                            img_count = len(listing_data.get('images', []))
                            amenity_count = len(listing_data.get('amenities', []))
                            print(f"    ✓ Saved to DB (ID: {listing_id[:8]}...) - {img_count} images, {amenity_count} amenities")
                        except Exception as e:
                            print(f"    ✗ Database error: {e}")
                            self.error_count += 1
                    else:
                        print(f"    ⚠ Skipping: Insufficient data")
                        self.error_count += 1
                    
                    # Respectful delay (luxury site, be extra careful)
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"    ✗ Error processing listing: {e}")
                    self.error_count += 1
                    continue
            
            # Print summary
            print("\n" + "=" * 60)
            print("SCRAPING COMPLETE")
            print("=" * 60)
            print(f"✓ Successfully inserted: {self.inserted_count} luxury listings")
            print(f"✗ Errors/Skipped: {self.error_count}")
            print(f"📸 Focus: Premium professional photography")
            print(f"🏆 Source: Sotheby's International Realty")
            print("=" * 60)
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    scraper = SothebyScraper(headless=True)
    scraper.scrape()

if __name__ == '__main__':
    main()
