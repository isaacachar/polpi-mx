#!/usr/bin/env python3
"""
Developer Properties Scraper for Polpi MX
Focuses on: TERRENOS (land), COMMERCIAL properties, and DEVELOPMENT opportunities
Target: 200+ terrenos, 100+ commercial
"""

import sys
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class DeveloperPropertiesScraper:
    """Scraper targeting DEVELOPERS, not homebuyers"""
    
    def __init__(self):
        """Initialize Chrome driver"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Disable images for faster loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.base_url = 'https://inmuebles.mercadolibre.com.mx'
        self.data_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/developer_properties'
        os.makedirs(self.data_dir, exist_ok=True)

    def get_search_urls(self, max_pages_per_category=20):
        """Generate search URLs for developer-focused properties"""
        urls = []
        
        # PRIORITY 1: TERRENOS (LAND) - highest priority for developers
        terreno_categories = [
            ('/terrenos/venta/distrito-federal/', 'sale', 'terreno', max_pages_per_category),
            # Additional terreno URLs with filters
            ('/terrenos/venta/distrito-federal/hasta-500-m2/', 'sale', 'terreno', 10),
            ('/terrenos/venta/distrito-federal/500-a-1000-m2/', 'sale', 'terreno', 10),
            ('/terrenos/venta/distrito-federal/mas-de-1000-m2/', 'sale', 'terreno', 10),
        ]
        
        # PRIORITY 2: COMMERCIAL PROPERTIES
        commercial_categories = [
            ('/oficinas/venta/distrito-federal/', 'sale', 'oficina', 15),
            ('/oficinas/renta/distrito-federal/', 'rental', 'oficina', 15),
            ('/locales/venta/distrito-federal/', 'sale', 'local_comercial', 15),
            ('/locales/renta/distrito-federal/', 'rental', 'local_comercial', 15),
            ('/bodegas/venta/distrito-federal/', 'sale', 'bodega', 10),
            ('/bodegas/renta/distrito-federal/', 'rental', 'bodega', 10),
        ]
        
        # PRIORITY 3: DEVELOPMENT OPPORTUNITIES
        development_categories = [
            ('/edificios/venta/distrito-federal/', 'sale', 'edificio', 10),
            ('/departamentos/venta/distrito-federal/mas-de-3-recamaras/', 'sale', 'multifamiliar', 5),
        ]
        
        all_categories = terreno_categories + commercial_categories + development_categories
        
        for base_path, listing_type, property_type, max_pages in all_categories:
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
            
            # Wait for page to load
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
        """Parse listing with focus on developer-relevant data"""
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
            
            # Attributes - with DEVELOPER FOCUS
            attributes = item_data.get('attributes', [])
            bedrooms = None
            bathrooms = None
            size_m2 = None
            lot_size_m2 = None  # Critical for terrenos
            parking_spaces = 0
            zoning_hints = []  # Extract zoning clues
            
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue
                
                attr_id = attr.get('id', '').lower()
                attr_name = attr.get('name', '').lower()
                attr_value = attr.get('value_name') or attr.get('value')
                attr_value_str = str(attr_value).lower()
                
                # Bedrooms
                if 'bedroom' in attr_id or 'recamara' in attr_id:
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
                
                # Size / Area - distinguish between built area and lot size
                elif any(x in attr_id for x in ['area', 'superficie', 'size']):
                    try:
                        size_match = re.search(r'[\d,]+', str(attr_value).replace(',', ''))
                        if size_match:
                            size_val = float(size_match.group())
                            
                            # For terrenos, this is lot size
                            if property_type == 'terreno':
                                lot_size_m2 = size_val
                            else:
                                # Check if it's lot vs built area
                                if 'terreno' in attr_name or 'lote' in attr_name:
                                    lot_size_m2 = size_val
                                elif 'construida' in attr_name or 'construccion' in attr_name:
                                    size_m2 = size_val
                                else:
                                    # Default to size_m2 if unclear
                                    if not size_m2:
                                        size_m2 = size_val
                    except:
                        pass
                
                # Parking
                elif 'parking' in attr_id or 'estacionamiento' in attr_id:
                    try:
                        parking_spaces = int(re.search(r'\d+', str(attr_value)).group())
                    except:
                        pass
                
                # Zoning hints (uso de suelo)
                elif any(x in attr_name for x in ['uso', 'zonificaci', 'tipo de uso']):
                    zoning_hints.append(attr_value_str)
            
            # Fallback: extract from title
            if not bedrooms or not size_m2:
                extracted = self.extract_from_text(title)
                if not bedrooms:
                    bedrooms = extracted.get('bedrooms')
                if not bathrooms:
                    bathrooms = extracted.get('bathrooms')
                if not size_m2 and not lot_size_m2:
                    size_m2 = extracted.get('size_m2')
            
            # For terrenos, size_m2 should be lot_size_m2
            if property_type == 'terreno' and size_m2 and not lot_size_m2:
                lot_size_m2 = size_m2
                size_m2 = None
            
            # Calculate price per m2 - critical for developers
            price_per_m2 = None
            if price_mxn:
                if lot_size_m2:
                    price_per_m2 = price_mxn / lot_size_m2
                elif size_m2:
                    price_per_m2 = price_mxn / size_m2
            
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
                'lot_size_m2': lot_size_m2,
                'city': city_name or 'Ciudad de Mexico',
                'colonia': neighborhood or address_line or None,
                'lat': lat,
                'lng': lng,
                'images': images,
                'parking_spaces': parking_spaces,
                'listing_type': listing_type,
                'raw_data': json.dumps({
                    'price_per_m2': price_per_m2,
                    'zoning_hints': zoning_hints
                })
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

    def scrape_all(self, max_listings=500):
        """Scrape all developer-focused categories"""
        urls = self.get_search_urls()
        all_listings = []
        stats_by_category = {}
        
        print(f"\n🏗️  DEVELOPER PROPERTIES SCRAPER")
        print(f"   Target: {len(urls)} pages")
        print(f"   Focus: TERRENOS (200+), COMMERCIAL (100+), DEVELOPMENT")
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
                # Skip duplicates silently
                if "UNIQUE constraint failed" not in str(e):
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
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        initial_terrenos = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type IN ("oficina", "local_comercial", "bodega", "edificio")')
        initial_commercial = cursor.fetchone()['count']
        
        conn.close()
        
        print("=" * 70)
        print(f"📊 INITIAL DATABASE")
        print(f"   Total: {initial_total}")
        print(f"   Terrenos: {initial_terrenos}")
        print(f"   Commercial: {initial_commercial}")
        print("=" * 70)
        
        # Scrape
        scraper = DeveloperPropertiesScraper()
        listings, stats_by_category = scraper.scrape_all(max_listings=500)
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPED {len(listings)} LISTINGS")
        for category, count in sorted(stats_by_category.items()):
            print(f"   {category}: {count}")
        print("=" * 70)
        
        if listings:
            print(f"\n💾 Storing in database...")
            stored = scraper.store_in_database(listings)
            print(f"   ✓ Stored {stored} new listings")
            
            # Sample by type
            terrenos = [l for l in listings if l.get('property_type') == 'terreno']
            commercial = [l for l in listings if l.get('property_type') in ['oficina', 'local_comercial', 'bodega', 'edificio']]
            
            if terrenos:
                print(f"\n🏞️  TERRENO SAMPLES:")
                for i, listing in enumerate(terrenos[:3], 1):
                    price = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                    lot_size = f"{listing.get('lot_size_m2'):,.0f} m²" if listing.get('lot_size_m2') else "N/A"
                    raw_data = json.loads(listing.get('raw_data', '{}'))
                    price_per_m2 = raw_data.get('price_per_m2')
                    price_per_m2_str = f"${price_per_m2:,.0f}/m²" if price_per_m2 else "N/A"
                    print(f"   {i}. {listing.get('title', '')[:50]}")
                    print(f"      {price} | {lot_size} | {price_per_m2_str}")
            
            if commercial:
                print(f"\n🏢 COMMERCIAL SAMPLES:")
                for i, listing in enumerate(commercial[:3], 1):
                    price = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                    size = f"{listing.get('size_m2'):,.0f} m²" if listing.get('size_m2') else "N/A"
                    print(f"   {i}. [{listing.get('property_type').upper()}] {listing.get('title', '')[:50]}")
                    print(f"      {price} | {size}")
        
        # Final stats
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        final_total = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        final_terrenos = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type IN ("oficina", "local_comercial", "bodega", "edificio")')
        final_commercial = cursor.fetchone()['count']
        
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL DATABASE")
        print(f"   Total: {final_total} (+{final_total - initial_total})")
        print(f"   Terrenos: {final_terrenos} (+{final_terrenos - initial_terrenos}) {'✓ GOAL!' if final_terrenos >= 200 else f'[Need {200 - final_terrenos} more]'}")
        print(f"   Commercial: {final_commercial} (+{final_commercial - initial_commercial}) {'✓ GOAL!' if final_commercial >= 100 else f'[Need {100 - final_commercial} more]'}")
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
