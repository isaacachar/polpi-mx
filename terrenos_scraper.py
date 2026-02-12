#!/usr/bin/env python3
"""
Terrenos (Land) Scraper - HIGHEST PRIORITY for developer platform
Target: 200+ land listings in CDMX with lot sizes and price per m²
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

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class TerrenosScraper:
    """Specialized scraper for land/terrenos targeting developers"""
    
    def __init__(self):
        """Initialize Chrome driver"""
        print("🌐 Initializing Chrome driver...")
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Disable images for speed
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.base_url = 'https://inmuebles.mercadolibre.com.mx'
        print("✓ Chrome driver ready\n")

    def get_terreno_urls(self, max_pages=25):
        """Generate terreno search URLs"""
        urls = []
        
        # Main terrenos search
        for page in range(1, max_pages + 1):
            offset = (page - 1) * 50
            if offset == 0:
                url = f"{self.base_url}/terrenos/venta/distrito-federal/"
            else:
                url = f"{self.base_url}/terrenos/venta/distrito-federal/_Desde_{offset}"
            
            urls.append({'url': url, 'page': page})
        
        return urls

    def extract_preloaded_state(self, url: str) -> Optional[Dict]:
        """Load page and extract data"""
        try:
            self.driver.get(url)
            time.sleep(4)  # Wait for JS to load
            
            script = "return window.__PRELOADED_STATE__ || window.__NEXT_DATA__ || null;"
            data = self.driver.execute_script(script)
            
            return data
            
        except Exception as e:
            print(f"  Error loading page: {e}")
            return None

    def parse_terreno(self, item: Dict) -> Optional[Dict]:
        """Parse terreno listing with developer focus"""
        try:
            listing_id = item.get('id')
            if not listing_id:
                return None
            
            title = item.get('title', '')
            
            # Price
            price_data = item.get('price', {})
            price_mxn = None
            if isinstance(price_data, dict):
                price_mxn = price_data.get('amount')
            elif isinstance(price_data, (int, float)):
                price_mxn = price_data
            
            if not price_mxn:
                return None  # Skip listings without price
            
            permalink = item.get('permalink', '')
            
            # Location
            location_data = item.get('location', {})
            city_name = None
            if isinstance(location_data.get('city'), dict):
                city_name = location_data['city'].get('name')
            
            neighborhood = None
            if isinstance(location_data.get('neighborhood'), dict):
                neighborhood = location_data['neighborhood'].get('name')
            
            lat = location_data.get('latitude')
            lng = location_data.get('longitude')
            
            # LOT SIZE - most important for terrenos
            attributes = item.get('attributes', [])
            lot_size_m2 = None
            
            for attr in attributes:
                if not isinstance(attr, dict):
                    continue
                
                attr_id = attr.get('id', '').lower()
                attr_name = attr.get('name', '').lower()
                attr_value = attr.get('value_name') or attr.get('value')
                
                # Look for area/superficie
                if any(x in attr_id for x in ['area', 'superficie', 'size']):
                    try:
                        size_match = re.search(r'[\d,]+', str(attr_value).replace(',', ''))
                        if size_match:
                            lot_size_m2 = float(size_match.group())
                    except:
                        pass
            
            # Fallback: extract from title
            if not lot_size_m2:
                size_match = re.search(r'([\d,]+)\s*m[²2]', title.lower())
                if size_match:
                    try:
                        lot_size_m2 = float(size_match.group(1).replace(',', ''))
                    except:
                        pass
            
            # Calculate price per m²
            price_per_m2 = None
            if lot_size_m2 and lot_size_m2 > 0:
                price_per_m2 = price_mxn / lot_size_m2
            
            # Images
            pictures = item.get('pictures', [])
            images = []
            if pictures:
                for pic in pictures[:3]:
                    if isinstance(pic, dict):
                        img_url = pic.get('url') or pic.get('secure_url')
                        if img_url:
                            images.append(img_url)
            
            listing = {
                'source': 'mercadolibre',
                'source_id': str(listing_id),
                'url': permalink,
                'title': title,
                'price_mxn': price_mxn,
                'property_type': 'terreno',
                'lot_size_m2': lot_size_m2,
                'city': city_name or 'Ciudad de Mexico',
                'colonia': neighborhood or None,
                'lat': lat,
                'lng': lng,
                'images': images,
                'listing_type': 'sale',
                'raw_data': json.dumps({
                    'price_per_m2': price_per_m2
                })
            }
            
            return listing
            
        except Exception as e:
            return None

    def scrape_page(self, search_info: Dict) -> List[Dict]:
        """Scrape single page"""
        url = search_info['url']
        page_num = search_info['page']
        
        print(f"📄 Page {page_num}: {url}")
        
        data = self.extract_preloaded_state(url)
        if not data:
            print(f"  ⚠ No data found")
            return []
        
        # Find results
        results = None
        if 'results' in data:
            results = data['results']
        elif 'items' in data:
            results = data['items']
        else:
            # Search nested
            for key in data.keys():
                if isinstance(data[key], dict):
                    if 'results' in data[key]:
                        results = data[key]['results']
                        break
                    elif 'items' in data[key]:
                        results = data[key]['items']
                        break
        
        if not results or not isinstance(results, list):
            print(f"  ⚠ No results array")
            return []
        
        print(f"  Found {len(results)} items on page")
        
        listings = []
        for item in results:
            if not isinstance(item, dict):
                continue
            
            listing = self.parse_terreno(item)
            if listing:
                listings.append(listing)
        
        print(f"  ✓ Extracted {len(listings)} valid terrenos")
        return listings

    def scrape_all(self, target_listings=250):
        """Scrape terrenos until target reached"""
        urls = self.get_terreno_urls()
        all_listings = []
        
        print(f"🏞️  TERRENOS SCRAPER FOR DEVELOPERS")
        print(f"   Target: {target_listings}+ land listings")
        print(f"   Max pages: {len(urls)}\n")
        
        for i, search_info in enumerate(urls):
            try:
                listings = self.scrape_page(search_info)
                all_listings.extend(listings)
                
                print(f"  Running total: {len(all_listings)}\n")
                
                if len(all_listings) >= target_listings:
                    print(f"✓ Reached target ({len(all_listings)} listings)")
                    break
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                continue
        
        return all_listings

    def store_in_database(self, listings: List[Dict]) -> int:
        """Store in database"""
        db = PolpiDB()
        stored = 0
        skipped = 0
        
        print(f"\n💾 Storing {len(listings)} listings in database...")
        
        for listing in listings:
            try:
                db.insert_listing(listing)
                stored += 1
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    skipped += 1
                else:
                    print(f"  Error: {e}")
        
        print(f"  ✓ Stored {stored} new listings")
        if skipped > 0:
            print(f"  ⊘ Skipped {skipped} duplicates")
        
        return stored

    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        # Initial stats
        db = PolpiDB()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        initial_total = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        initial_terrenos = cursor.fetchone()['count']
        
        conn.close()
        
        print("=" * 70)
        print(f"📊 INITIAL DATABASE")
        print(f"   Total listings: {initial_total}")
        print(f"   Terrenos: {initial_terrenos}")
        print(f"   GOAL: 200+ terrenos")
        print("=" * 70 + "\n")
        
        # Scrape
        scraper = TerrenosScraper()
        listings = scraper.scrape_all(target_listings=250)
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPED {len(listings)} TERRENOS")
        print("=" * 70)
        
        if listings:
            # Show samples
            print(f"\n🏞️  SAMPLE TERRENOS:")
            for i, listing in enumerate(listings[:5], 1):
                price = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                lot_size = f"{listing.get('lot_size_m2'):,.0f} m²" if listing.get('lot_size_m2') else "N/A"
                raw_data = json.loads(listing.get('raw_data', '{}'))
                price_per_m2 = raw_data.get('price_per_m2')
                price_per_m2_str = f"${price_per_m2:,.0f}/m²" if price_per_m2 else "N/A"
                colonia = listing.get('colonia', 'N/A')
                
                print(f"\n   {i}. {listing.get('title', '')[:60]}")
                print(f"      💰 {price}")
                print(f"      📏 {lot_size}")
                print(f"      📊 {price_per_m2_str}")
                print(f"      📍 {colonia}")
            
            # Store
            stored = scraper.store_in_database(listings)
        
        # Final stats
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM listings')
        final_total = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM listings WHERE property_type = "terreno"')
        final_terrenos = cursor.fetchone()['count']
        
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL DATABASE")
        print(f"   Total: {final_total} (+{final_total - initial_total})")
        print(f"   Terrenos: {final_terrenos} (+{final_terrenos - initial_terrenos})")
        
        if final_terrenos >= 200:
            print(f"   ✅ GOAL ACHIEVED! {final_terrenos} terrenos")
        else:
            print(f"   📈 Progress: {final_terrenos}/200 ({(final_terrenos/200*100):.1f}%)")
        
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
