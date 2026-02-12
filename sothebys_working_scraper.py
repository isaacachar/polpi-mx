#!/usr/bin/env python3
"""
Working Sotheby's scraper - CDMX luxury listings with high-quality images
Simplified and tested approach
"""

import sys
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class SothebysWorkingScraper:
    def __init__(self, max_listings=50):
        self.db = PolpiDB()
        self.inserted = 0
        self.errors = 0
        self.max_listings = max_listings
        
    def init_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=options)
        
    def get_listing_urls(self):
        """Get property URLs from search pages"""
        print("\n📋 Collecting listing URLs...")
        
        search_urls = [
            'https://www.sothebysrealty.com/eng/sales/mexico-city-cm-mex',
            'https://www.sothebysrealty.com/eng/sales/cm-mex',
        ]
        
        all_urls = set()
        
        for search_url in search_urls:
            try:
                print(f"  Checking: {search_url}")
                self.driver.get(search_url)
                time.sleep(7)  # Wait for luxury site
                
                # Find property links
                links = re.findall(r'href=\"(/eng/sales/detail/[^\"]+)\"', self.driver.page_source)
                mexico_links = [f"https://www.sothebysrealty.com{l}" for l in links if 'mexico-city-cm' in l]
                
                all_urls.update(mexico_links)
                print(f"    Found {len(mexico_links)} listings")
                
            except Exception as e:
                print(f"    Error: {e}")
                continue
        
        unique_urls = list(set(all_urls))
        print(f"\n✓ Total unique listings: {len(unique_urls)}")
        return unique_urls[:self.max_listings]
    
    def scrape_listing(self, url):
        """Scrape single listing with focus on images"""
        try:
            print(f"\n  → {url}")
            self.driver.get(url)
            time.sleep(4)
            
            data = {
                'source': 'sothebys',
                'url': url,
                'source_id': url.split('/')[-2] if '/' in url else None,
                'city': 'Ciudad de México',
            }
            
            # Title
            try:
                title = self.driver.find_element(By.TAG_NAME, 'h1').text.strip()
                data['title'] = title if title else "Sotheby's Luxury Property"
            except:
                data['title'] = "Sotheby's Luxury Property"
            
            # Extract colonia from URL or title
            url_parts = url.lower().split('/')
            for part in url_parts:
                if any(hood in part for hood in ['polanco', 'lomas', 'roma', 'condesa', 'chapultepec', 'bosques']):
                    data['colonia'] = part.replace('-', ' ').title()
                    break
            
            # Price - try multiple approaches
            try:
                # Method 1: Look for price in meta tags
                price_meta = self.driver.find_elements(By.CSS_SELECTOR, 'meta[property="og:price:amount"]')
                if price_meta:
                    price = float(price_meta[0].get_attribute('content'))
                    currency = self.driver.find_elements(By.CSS_SELECTOR, 'meta[property="og:price:currency"]')
                    if currency and 'USD' in currency[0].get_attribute('content'):
                        data['price_usd'] = price
                        data['price_mxn'] = price * 17  # Approximate conversion
                    else:
                        data['price_mxn'] = price
                
                # Method 2: Look in page text
                if not data.get('price_mxn'):
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    price_matches = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:USD|MXN|Million))?', page_text)
                    if price_matches:
                        price_text = price_matches[0]
                        price_num = float(price_text.replace('$', '').replace(',', '').split()[0])
                        if 'Million' in price_text or price_num < 100:
                            price_num *= 1_000_000
                        if 'USD' in price_text:
                            data['price_usd'] = price_num
                            data['price_mxn'] = price_num * 17
                        else:
                            data['price_mxn'] = price_num
            except Exception as e:
                print(f"      ⚠ Could not extract price: {e}")
            
            # Details (beds, baths, size)
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                
                # Bedrooms
                bed_match = re.search(r'(\d+)\s*(?:Bed|Bedroom|Recámara)', body_text, re.IGNORECASE)
                if bed_match:
                    data['bedrooms'] = int(bed_match.group(1))
                
                # Bathrooms
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:Bath|Bathroom|Baño)', body_text, re.IGNORECASE)
                if bath_match:
                    data['bathrooms'] = int(float(bath_match.group(1)))
                
                # Size
                size_match = re.search(r'([\d,]+)\s*(?:sq\s*ft|Sq\.\s*Ft\.)', body_text, re.IGNORECASE)
                if size_match:
                    sqft = float(size_match.group(1).replace(',', ''))
                    data['size_m2'] = int(sqft * 0.092903)
                
                # Try metric
                if not data.get('size_m2'):
                    size_match = re.search(r'([\d,]+)\s*m[²2]', body_text, re.IGNORECASE)
                    if size_match:
                        data['size_m2'] = int(size_match.group(1).replace(',', ''))
            except:
                pass
            
            # Property type
            title_lower = data['title'].lower()
            if any(w in title_lower for w in ['condo', 'apartment', 'penthouse', 'departamento']):
                data['property_type'] = 'departamento'
            elif any(w in title_lower for w in ['land', 'lot', 'terreno']):
                data['property_type'] = 'terreno'
            else:
                data['property_type'] = 'casa'
            
            # IMAGES - Priority!
            images = []
            try:
                # Method 1: Look for image tags
                img_elements = self.driver.find_elements(By.TAG_NAME, 'img')
                for img in img_elements:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and 'sothebys' in src and 'http' in src:
                        # Filter out small images
                        if not any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'thumb']):
                            # Try to get high-res version
                            src = re.sub(r'/\d+x\d+/', '/1920x1080/', src)
                            src = src.replace('_small', '_large').replace('_thumb', '_large')
                            if src not in images:
                                images.append(src)
                
                # Method 2: Check for JSON-LD structured data
                scripts = self.driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                for script in scripts:
                    try:
                        json_data = json.loads(script.get_attribute('innerHTML'))
                        if 'image' in json_data:
                            img = json_data['image']
                            if isinstance(img, str):
                                images.append(img)
                            elif isinstance(img, list):
                                images.extend(img)
                    except:
                        pass
                
                data['images'] = list(set(images))[:25]  # Dedupe and limit
                print(f"      ✓ {len(data['images'])} images")
                
            except Exception as e:
                print(f"      ⚠ Image extraction error: {e}")
                data['images'] = []
            
            # Description
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, '[class*="description"], [class*="remark"]')
                data['description'] = desc_elem.text.strip()[:1500]
            except:
                pass
            
            data['listing_type'] = 'sale'  # Sotheby's is almost always sales
            
            return data
            
        except Exception as e:
            print(f"      ✗ Error: {e}")
            return None
    
    def scrape(self):
        """Main scraping method"""
        print("=" * 60)
        print("Sotheby's Mexico City Scraper")
        print("Focus: Luxury listings with professional photography")
        print("=" * 60)
        
        try:
            self.init_driver()
            
            # Get listing URLs
            urls = self.get_listing_urls()
            
            if not urls:
                print("\n⚠ No listings found!")
                return
            
            # Scrape each listing
            print(f"\n📸 Scraping {len(urls)} luxury listings...")
            
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}]")
                
                try:
                    data = self.scrape_listing(url)
                    
                    if data and data.get('title'):
                        # Require minimum data
                        if not data.get('price_mxn') and not data.get('price_usd'):
                            print("      ⚠ Skipping - no price")
                            self.errors += 1
                            continue
                        
                        # Save to database
                        try:
                            listing_id = self.db.insert_listing(data)
                            self.inserted += 1
                            img_count = len(data.get('images', []))
                            price = data.get('price_mxn', data.get('price_usd', 0))
                            print(f"      ✓ Saved! ${price:,.0f} MXN - {img_count} images")
                        except Exception as e:
                            print(f"      ✗ DB error: {e}")
                            self.errors += 1
                    else:
                        self.errors += 1
                    
                    # Respectful delay
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"      ✗ Error: {e}")
                    self.errors += 1
            
            # Summary
            print("\n" + "=" * 60)
            print("SCRAPING COMPLETE")
            print("=" * 60)
            print(f"✓ Successfully saved: {self.inserted} listings")
            print(f"✗ Errors/skipped: {self.errors}")
            print("=" * 60)
            
            # Check image quality
            if self.inserted > 0:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*), AVG(LENGTH(images)) as avg_img_data
                    FROM listings 
                    WHERE source = 'sothebys' AND images IS NOT NULL AND images != '[]'
                """)
                result = cursor.fetchone()
                conn.close()
                
                print(f"\n📊 Image Quality Check:")
                print(f"   Listings with images: {result['COUNT(*)']}")
                print(f"   Avg image data size: {result['avg_img_data']:.0f} bytes")
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    # Scrape up to 50 luxury listings
    scraper = SothebysWorkingScraper(max_listings=50)
    scraper.scrape()

if __name__ == '__main__':
    main()
