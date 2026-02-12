#!/usr/bin/env python3
"""MercadoLibre Scraper using undetected-chromedriver to bypass bot detection"""

import sys
import json
import re
import hashlib
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class MercadoLibreScraper:
    def __init__(self):
        """Initialize undetected Chrome driver"""
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Disable images for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        self.driver = uc.Chrome(options=options, version_main=144)
        self.base_url = 'https://inmuebles.mercadolibre.com.mx'
        self.data_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/mercadolibre'
        os.makedirs(self.data_dir, exist_ok=True)

    def get_search_urls(self, pages_per_category=10):
        """Generate search URLs for CDMX properties"""
        urls = []
        
        categories = [
            ('/departamentos/venta/distrito-federal/', 'sale', 'departamento', pages_per_category),
            ('/departamentos/renta/distrito-federal/', 'rental', 'departamento', pages_per_category),
            ('/casas/venta/distrito-federal/', 'sale', 'casa', pages_per_category),
            ('/casas/renta/distrito-federal/', 'rental', 'casa', pages_per_category),
            ('/terrenos/venta/distrito-federal/', 'sale', 'terreno', min(5, pages_per_category)),
        ]
        
        for base_path, listing_type, property_type, max_pages in categories:
            for page in range(1, max_pages + 1):
                offset = (page - 1) * 50
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
        """Load page and extract window.__PRELOADED_STATE__"""
        try:
            print(f"  Loading: {url}")
            self.driver.get(url)
            
            # Wait for page to load - try multiple times
            max_attempts = 3
            for attempt in range(max_attempts):
                time.sleep(5 if attempt == 0 else 3)
                
                # Check for error page
                if "Hubo un error" in self.driver.page_source:
                    print(f"  ⚠ Error page detected, attempt {attempt + 1}/{max_attempts}")
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        self.driver.refresh()
                        continue
                    else:
                        return None
                
                # Try to extract preloaded state
                script = "return window.__PRELOADED_STATE__ || window.__NEXT_DATA__ || null;"
                preloaded_state = self.driver.execute_script(script)
                
                if preloaded_state:
                    print(f"  ✓ Found data object")
                    return preloaded_state
            
            print(f"  ⚠ No data object found after {max_attempts} attempts")
            return None
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def parse_listing_from_state(self, item_data: Dict, listing_type: str, property_type: str) -> Optional[Dict]:
        """Parse listing from data object"""
        try:
            listing_id = item_data.get('id')
            if not listing_id:
                return None
            
            title = item_data.get('title', '')
            
            # Price
            price_data = item_data.get('price', {})
            price_mxn = None
            if isinstance(price_data, dict):
                price_mxn = price_data.get('amount')
            elif isinstance(price_data, (int, float)):
                price_mxn = price_data
            
            # URL
            permalink = item_data.get('permalink', '')
            
            # Images
            pictures = item_data.get('pictures', [])
            images = []
            if pictures:
                for pic in pictures[:3]:
                    if isinstance(pic, dict):
                        img_url = pic.get('url') or pic.get('secure_url')
                        if img_url:
                            images.append(img_url)
            
            # Location
            location_data = item_data.get('location', {})
            city_name = None
            if isinstance(location_data.get('city'), dict):
                city_name = location_data['city'].get('name')
            
            neighborhood = None
            if isinstance(location_data.get('neighborhood'), dict):
                neighborhood = location_data['neighborhood'].get('name')
            
            address_line = location_data.get('address_line', '')
            
            lat = location_data.get('latitude')
            lng = location_data.get('longitude')
            
            # Attributes
            attributes = item_data.get('attributes', [])
            bedrooms = None
            bathrooms = None
            size_m2 = None
            parking_spaces = 0
            
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue
                
                attr_id = attr.get('id', '').lower()
                attr_value = attr.get('value_name') or attr.get('value')
                
                if 'bedroom' in attr_id or 'recamara' in attr_id:
                    try:
                        bedrooms = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
                elif 'bathroom' in attr_id or 'baño' in attr_id or 'bano' in attr_id:
                    try:
                        bathrooms = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
                elif any(x in attr_id for x in ['area', 'superficie', 'size']):
                    try:
                        size_match = re.search(r'[\d,]+', str(attr_value).replace(',', ''))
                        if size_match:
                            size_m2 = float(size_match.group())
                    except:
                        pass
                elif 'parking' in attr_id or 'estacionamiento' in attr_id:
                    try:
                        parking_spaces = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
            
            # Fallback: extract from title
            if not bedrooms or not size_m2:
                extracted = self.extract_from_text(title)
                if not bedrooms:
                    bedrooms = extracted.get('bedrooms')
                if not bathrooms:
                    bathrooms = extracted.get('bathrooms')
                if not size_m2:
                    size_m2 = extracted.get('size_m2')
            
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
                'images': images,
                'parking_spaces': parking_spaces,
                'listing_type': listing_type,
            }
            
            return listing
            
        except Exception as e:
            print(f"    Error parsing listing: {e}")
            return None

    def extract_from_text(self, text: str) -> Dict:
        """Extract property details from text"""
        text = text.lower()
        details = {}
        
        bed_match = re.search(r'(\d+)\s*(?:rec[aá]mara|habitaci[oó]n|dormitorio|bedroom)', text)
        if bed_match:
            details['bedrooms'] = int(bed_match.group(1))
        
        bath_match = re.search(r'(\d+)\s*(?:ba[ñn]o|bathroom)', text)
        if bath_match:
            details['bathrooms'] = int(bath_match.group(1))
        
        size_match = re.search(r'([\d,]+)\s*m[²2]', text)
        if size_match:
            try:
                details['size_m2'] = float(size_match.group(1).replace(',', ''))
            except:
                pass
        
        return details

    def scrape_page(self, search_info: Dict) -> List[Dict]:
        """Scrape a single page"""
        url = search_info['url']
        listing_type = search_info['listing_type']
        property_type = search_info['property_type']
        
        print(f"[{search_info['category']}] Page {search_info['page']}")
        
        preloaded_state = self.extract_preloaded_state(url)
        if not preloaded_state:
            return []
        
        listings = []
        
        # Find results in the data structure
        results = None
        if 'results' in preloaded_state:
            results = preloaded_state['results']
        elif 'items' in preloaded_state:
            results = preloaded_state['items']
        elif 'searchResults' in preloaded_state:
            search_results = preloaded_state['searchResults']
            if isinstance(search_results, dict):
                results = search_results.get('results') or search_results.get('items')
        
        # Search nested structure
        if not results:
            for key in preloaded_state.keys():
                if isinstance(preloaded_state[key], dict):
                    if 'results' in preloaded_state[key]:
                        results = preloaded_state[key]['results']
                        break
                    elif 'items' in preloaded_state[key]:
                        results = preloaded_state[key]['items']
                        break
        
        if not results or not isinstance(results, list):
            print(f"  ⚠ No results array found")
            return []
        
        print(f"  Found {len(results)} items")
        
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
        
        print(f"\n🛒 MercadoLibre Scraper (Undetected ChromeDriver)")
        print(f"   Target: {len(urls)} pages, {len(set(u['category'] for u in urls))} categories")
        print(f"   Goal: {max_listings}+ listings\n")
        
        for i, search_info in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}]", end=" ")
            
            try:
                listings = self.scrape_page(search_info)
                all_listings.extend(listings)
                
                category = search_info['category']
                stats_by_category[category] = stats_by_category.get(category, 0) + len(listings)
                
                print(f"  Total: {len(all_listings)}")
                
                if len(all_listings) >= max_listings:
                    print(f"\n✓ Reached goal ({len(all_listings)} listings)")
                    break
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
        
        return all_listings, stats_by_category

    def store_in_database(self, listings: List[Dict]) -> int:
        """Store listings in database"""
        db = PolpiDB()
        stored = 0
        
        for listing in listings:
            try:
                db.insert_listing(listing)
                stored += 1
            except Exception as e:
                print(f"  Error storing listing {listing.get('source_id')}: {e}")
                continue
        
        return stored

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        # Database stats before
        db = PolpiDB()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        initial_total = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
        initial_ml = cursor.fetchone()['count']
        conn.close()
        
        print("=" * 70)
        print(f"📊 INITIAL DATABASE")
        print(f"   Total: {initial_total} | MercadoLibre: {initial_ml}")
        print("=" * 70)
        
        # Scrape
        scraper = MercadoLibreScraper()
        listings, stats_by_category = scraper.scrape_all(pages_per_category=10, max_listings=500)
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPED {len(listings)} LISTINGS")
        for category, count in sorted(stats_by_category.items()):
            print(f"   {category}: {count}")
        print("=" * 70)
        
        if listings:
            print(f"\n💾 Storing in database...")
            stored = scraper.store_in_database(listings)
            print(f"   ✓ Stored {stored} listings")
            
            # Sample
            print(f"\n🏠 SAMPLE:")
            for i, listing in enumerate(listings[:3], 1):
                price = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                type_str = f"{listing.get('listing_type')} {listing.get('property_type')}"
                print(f"   {i}. [{type_str.upper()}] {listing.get('title', '')[:50]}")
                print(f"      {price} | {listing.get('bedrooms', 'N/A')} bed | {listing.get('size_m2', 'N/A')} m²")
        
        # Final stats
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        final_total = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE source = "mercadolibre"')
        final_ml = cursor.fetchone()['count']
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL DATABASE")
        print(f"   Total: {final_total} (+{final_total - initial_total})")
        print(f"   MercadoLibre: {final_ml} (+{final_ml - initial_ml})")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if scraper:
            scraper.close()

if __name__ == '__main__':
    main()
