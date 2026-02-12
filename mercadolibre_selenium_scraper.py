#!/usr/bin/env python3
"""MercadoLibre Selenium Scraper - Extracts data from window.__PRELOADED_STATE__"""

import sys
import json
import re
import hashlib
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class MercadoLibreSeleniumScraper:
    def __init__(self, headless=True):
        """Initialize Selenium scraper with Chrome"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        
        # Speed up by disabling images
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use 'none' page load strategy to not wait for full page load
        chrome_options.page_load_strategy = 'none'
        
        # Initialize driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(60)
        
        self.base_url = 'https://inmuebles.mercadolibre.com.mx'
        self.data_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/mercadolibre'
        os.makedirs(self.data_dir, exist_ok=True)

    def get_search_urls(self, pages_per_category=10):
        """Generate search URLs for CDMX properties"""
        urls = []
        
        # Categories: (path, listing_type, property_type, pages)
        categories = [
            ('/departamentos/venta/distrito-federal/', 'sale', 'departamento', pages_per_category),
            ('/departamentos/renta/distrito-federal/', 'rental', 'departamento', pages_per_category),
            ('/casas/venta/distrito-federal/', 'sale', 'casa', pages_per_category),
            ('/casas/renta/distrito-federal/', 'rental', 'casa', pages_per_category),
            ('/terrenos/venta/distrito-federal/', 'sale', 'terreno', min(5, pages_per_category)),
        ]
        
        for base_path, listing_type, property_type, max_pages in categories:
            for page in range(1, max_pages + 1):
                offset = (page - 1) * 50  # MercadoLibre uses 50 items per page
                if offset == 0:
                    url = f"{self.base_url}{base_path}"
                else:
                    url = f"{self.base_url}{base_path}_Desde_{offset}"
                
                urls.append({
                    'url': url,
                    'listing_type': listing_type,
                    'property_type': property_type,
                    'page': page,
                    'category': f"{listing_type}_{property_type}"
                })
        
        return urls

    def extract_preloaded_state(self, url: str) -> Optional[Dict]:
        """Load page with Selenium and extract window.__PRELOADED_STATE__"""
        try:
            print(f"  Loading: {url}")
            self.driver.get(url)
            
            # Wait for the __PRELOADED_STATE__ to be available
            # Since we're using page_load_strategy='none', we need to wait manually
            max_wait = 15
            wait_interval = 0.5
            elapsed = 0
            preloaded_state = None
            
            while elapsed < max_wait:
                try:
                    # Check if __PRELOADED_STATE__ is available
                    script = """
                    return window.__PRELOADED_STATE__ || window.__PRELOADED_STATES__ || null;
                    """
                    preloaded_state = self.driver.execute_script(script)
                    
                    if preloaded_state:
                        break
                    
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception:
                    time.sleep(wait_interval)
                    elapsed += wait_interval
            
            if preloaded_state:
                # Save raw data for debugging (only first few pages to save space)
                if len(os.listdir(self.data_dir)) < 5:
                    timestamp = int(time.time())
                    filename = f"preloaded_state_{timestamp}.json"
                    filepath = os.path.join(self.data_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(preloaded_state, f, indent=2, ensure_ascii=False)
                    print(f"  ✓ Saved preloaded state to {filename}")
                return preloaded_state
            else:
                print(f"  ⚠ Could not find __PRELOADED_STATE__ after {max_wait}s")
                return None
            
        except Exception as e:
            print(f"  ✗ Error loading page: {e}")
            return None

    def parse_listing_from_state(self, item_data: Dict, listing_type: str, property_type: str) -> Optional[Dict]:
        """Parse a single listing from __PRELOADED_STATE__ data"""
        try:
            # MercadoLibre's data structure can vary, so we'll try multiple paths
            listing_id = item_data.get('id')
            if not listing_id:
                return None
            
            # Extract basic info
            title = item_data.get('title', '')
            price_data = item_data.get('price', {})
            price_mxn = None
            
            if isinstance(price_data, dict):
                price_mxn = price_data.get('amount')
            elif isinstance(price_data, (int, float)):
                price_mxn = price_data
            
            # Get URL
            permalink = item_data.get('permalink', '')
            
            # Get images
            pictures = item_data.get('pictures', [])
            images = []
            if pictures:
                for pic in pictures[:3]:
                    if isinstance(pic, dict):
                        img_url = pic.get('url') or pic.get('secure_url')
                        if img_url:
                            images.append(img_url)
                    elif isinstance(pic, str):
                        images.append(pic)
            
            # Get location
            location_data = item_data.get('location', {})
            city_name = location_data.get('city', {}).get('name') if isinstance(location_data.get('city'), dict) else None
            state_name = location_data.get('state', {}).get('name') if isinstance(location_data.get('state'), dict) else None
            
            # Try to get colonia/neighborhood
            neighborhood = location_data.get('neighborhood', {}).get('name') if isinstance(location_data.get('neighborhood'), dict) else None
            address_line = location_data.get('address_line', '')
            
            # Get coordinates
            lat = None
            lng = None
            if 'latitude' in location_data:
                lat = location_data.get('latitude')
                lng = location_data.get('longitude')
            
            # Get attributes (bedrooms, bathrooms, size)
            attributes = item_data.get('attributes', [])
            bedrooms = None
            bathrooms = None
            size_m2 = None
            parking_spaces = 0
            
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue
                    
                attr_id = attr.get('id', '').lower()
                attr_name = attr.get('name', '').lower()
                attr_value = attr.get('value_name') or attr.get('value')
                
                # Bedrooms
                if 'bedroom' in attr_id or 'recamara' in attr_id or 'habitacion' in attr_name:
                    try:
                        bedrooms = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
                
                # Bathrooms
                elif 'bathroom' in attr_id or 'baño' in attr_id or 'bano' in attr_id:
                    try:
                        bathrooms = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
                
                # Size
                elif any(x in attr_id for x in ['area', 'superficie', 'size']) or 'm²' in str(attr_value).lower():
                    try:
                        size_match = re.search(r'[\d,]+', str(attr_value).replace(',', ''))
                        if size_match:
                            size_m2 = float(size_match.group())
                    except:
                        pass
                
                # Parking
                elif 'parking' in attr_id or 'estacionamiento' in attr_id or 'cochera' in attr_name:
                    try:
                        parking_spaces = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
            
            # Fallback: extract from title if attributes not found
            if not bedrooms or not bathrooms or not size_m2:
                extracted = self.extract_from_text(title)
                if not bedrooms:
                    bedrooms = extracted.get('bedrooms')
                if not bathrooms:
                    bathrooms = extracted.get('bathrooms')
                if not size_m2:
                    size_m2 = extracted.get('size_m2')
            
            # Get description
            description = ''
            if 'descriptions' in item_data and item_data['descriptions']:
                desc_data = item_data['descriptions']
                if isinstance(desc_data, list) and desc_data:
                    description = desc_data[0].get('text', '') if isinstance(desc_data[0], dict) else ''
                elif isinstance(desc_data, str):
                    description = desc_data
            
            # Build listing object
            listing = {
                'source': 'mercadolibre',
                'source_id': str(listing_id),
                'url': permalink,
                'title': title,
                'price_mxn': price_mxn,
                'property_type': property_type,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'size_m2': size_m2,
                'city': city_name or 'Ciudad de Mexico',
                'colonia': neighborhood or address_line or None,
                'lat': lat,
                'lng': lng,
                'description': description[:500] if description else '',
                'images': images,
                'parking_spaces': parking_spaces,
                'listing_type': listing_type,
                'raw_data': item_data
            }
            
            return listing
            
        except Exception as e:
            print(f"    Error parsing listing: {e}")
            return None

    def extract_from_text(self, text: str) -> Dict:
        """Extract property details from text"""
        text = text.lower()
        details = {
            'bedrooms': None,
            'bathrooms': None,
            'size_m2': None
        }
        
        # Bedrooms
        bed_match = re.search(r'(\d+)\s*(?:rec[aá]mara|habitaci[oó]n|dormitorio|bedroom|hab)', text)
        if bed_match:
            details['bedrooms'] = int(bed_match.group(1))
        
        # Bathrooms
        bath_match = re.search(r'(\d+)\s*(?:ba[ñn]o|bathroom)', text)
        if bath_match:
            details['bathrooms'] = int(bath_match.group(1))
        
        # Size
        size_match = re.search(r'([\d,]+)\s*m[²2]', text)
        if size_match:
            try:
                details['size_m2'] = float(size_match.group(1).replace(',', ''))
            except:
                pass
        
        return details

    def scrape_page(self, search_info: Dict) -> List[Dict]:
        """Scrape a single search page"""
        url = search_info['url']
        listing_type = search_info['listing_type']
        property_type = search_info['property_type']
        
        print(f"[{search_info['category']}] Page {search_info['page']}")
        
        preloaded_state = self.extract_preloaded_state(url)
        if not preloaded_state:
            return []
        
        listings = []
        
        # Try different paths in the state object
        results = None
        
        # Common paths where listings are stored
        if 'results' in preloaded_state:
            results = preloaded_state['results']
        elif 'items' in preloaded_state:
            results = preloaded_state['items']
        elif 'searchResults' in preloaded_state:
            search_results = preloaded_state['searchResults']
            if isinstance(search_results, dict):
                results = search_results.get('results') or search_results.get('items')
            else:
                results = search_results
        
        # Navigate nested structure
        for key in preloaded_state.keys():
            if results:
                break
            if isinstance(preloaded_state[key], dict):
                if 'results' in preloaded_state[key]:
                    results = preloaded_state[key]['results']
                elif 'items' in preloaded_state[key]:
                    results = preloaded_state[key]['items']
        
        if not results or not isinstance(results, list):
            print(f"  ⚠ No results found in preloaded state")
            return []
        
        print(f"  Found {len(results)} items in preloaded state")
        
        for item_data in results:
            if not isinstance(item_data, dict):
                continue
            
            listing = self.parse_listing_from_state(item_data, listing_type, property_type)
            if listing and listing.get('price_mxn'):
                listings.append(listing)
        
        print(f"  ✓ Extracted {len(listings)} valid listings")
        return listings

    def scrape_all(self, pages_per_category=10, max_listings=500):
        """Scrape all categories"""
        urls = self.get_search_urls(pages_per_category)
        all_listings = []
        stats_by_category = {}
        
        print(f"\n🛒 Starting MercadoLibre Selenium Scraper")
        print(f"   Target: {len(urls)} pages across {len(set(u['category'] for u in urls))} categories")
        print(f"   Goal: {max_listings}+ listings\n")
        
        for i, search_info in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}]", end=" ")
            
            try:
                listings = self.scrape_page(search_info)
                all_listings.extend(listings)
                
                # Track stats
                category = search_info['category']
                if category not in stats_by_category:
                    stats_by_category[category] = 0
                stats_by_category[category] += len(listings)
                
                print(f"  Total so far: {len(all_listings)} listings")
                
                # Stop if we hit the goal
                if len(all_listings) >= max_listings:
                    print(f"\n✓ Reached {max_listings}+ listings goal ({len(all_listings)})")
                    break
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        return all_listings, stats_by_category

    def store_in_database(self, listings: List[Dict]) -> int:
        """Store listings in database"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Convert images list to JSON string
                if 'images' in listing and isinstance(listing['images'], list):
                    listing['images'] = json.dumps(listing['images'])
                
                # Generate ID if not exists
                if 'id' not in listing:
                    id_string = f"{listing['source']}_{listing.get('source_id', '')}_{listing.get('url', '')}"
                    listing['id'] = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Add timestamp
                listing['scraped_date'] = datetime.now().isoformat()
                
                # Remove raw_data before storing (it's too large)
                listing.pop('raw_data', None)
                
                # Use database insert method
                db.insert_listing(listing)
                stored_count += 1
                
            except Exception as e:
                print(f"  Error storing listing: {e}")
                continue
        
        return stored_count

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        # Initialize scraper
        scraper = MercadoLibreSeleniumScraper(headless=True)
        
        # Get initial database stats
        db = PolpiDB()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        initial_total = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
        initial_ml = cursor.fetchone()['count']
        conn.close()
        
        print("=" * 70)
        print(f"📊 INITIAL DATABASE STATUS")
        print(f"   Total listings: {initial_total}")
        print(f"   MercadoLibre listings: {initial_ml}")
        print("=" * 70)
        
        # Scrape listings
        listings, stats_by_category = scraper.scrape_all(pages_per_category=10, max_listings=500)
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPING RESULTS")
        print(f"   Total scraped: {len(listings)}")
        print(f"\n   By category:")
        for category, count in sorted(stats_by_category.items()):
            print(f"      {category}: {count}")
        print("=" * 70)
        
        if listings:
            # Store in database
            print(f"\n💾 Storing {len(listings)} listings in database...")
            stored = scraper.store_in_database(listings)
            print(f"   ✓ Stored {stored} listings")
            
            # Show sample
            print(f"\n🏠 SAMPLE LISTINGS:")
            for i, listing in enumerate(listings[:5], 1):
                price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                type_str = f"{listing.get('listing_type', '').upper()} {listing.get('property_type', '')}"
                beds = listing.get('bedrooms', 'N/A')
                baths = listing.get('bathrooms', 'N/A')
                size = listing.get('size_m2', 'N/A')
                print(f"   {i}. [{type_str}] {listing.get('title', '')[:60]}")
                print(f"      {price_str} | {beds} bed | {baths} bath | {size} m²")
        
        # Final database stats
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        final_total = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
        final_ml = cursor.fetchone()['count']
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL DATABASE STATUS")
        print(f"   Total listings: {final_total} (+{final_total - initial_total})")
        print(f"   MercadoLibre: {final_ml} (+{final_ml - initial_ml})")
        print("=" * 70)
        
        return final_total
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if scraper:
            scraper.close()

if __name__ == '__main__':
    main()
