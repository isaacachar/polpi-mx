#!/usr/bin/env python3
"""
Lamudi Developer-Focused Scraper
ONLY scrapes: TERRENOS (land) and COMMERCIAL properties
Skips residential (casas/departamentos) for speed
"""

import sys
import json
import re
import time
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class LamudiDeveloperScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9',
        })
        self.base_url = 'https://www.lamudi.com.mx'

    def get_developer_urls(self):
        """Get URLs for TERRENOS and COMMERCIAL only"""
        urls = []
        
        # TERRENOS (LAND) - Priority 1
        terreno_urls = [
            ('/terreno/for-sale/', 'terreno', 10),  # Increased pages
            ('/lote/for-sale/', 'terreno', 5),
        ]
        
        for base_path, prop_type, max_pages in terreno_urls:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('sale', prop_type, self.base_url + base_path))
                else:
                    urls.append(('sale', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        # COMMERCIAL - Priority 2
        commercial_urls = [
            ('/local-comercial/for-sale/', 'local_comercial', 8),
            ('/oficina/for-sale/', 'oficina', 8),
            ('/bodega/for-sale/', 'bodega', 5),
            ('/edificio/for-sale/', 'edificio', 5),
            ('/local-comercial/for-rent/', 'local_comercial', 5),
            ('/oficina/for-rent/', 'oficina', 5),
        ]
        
        for base_path, prop_type, max_pages in commercial_urls:
            for page in range(1, max_pages + 1):
                listing_type = 'rental' if 'rent' in base_path else 'sale'
                if page == 1:
                    urls.append((listing_type, prop_type, self.base_url + base_path))
                else:
                    urls.append((listing_type, prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        return urls

    def is_cdmx(self, address_data):
        """Check if property is in CDMX"""
        if not isinstance(address_data, dict):
            return False
        
        full_address = ' '.join(str(v).lower() for v in address_data.values())
        
        cdmx_terms = ['ciudad de méxico', 'cdmx', 'miguel hidalgo', 'benito juárez', 
                      'cuauhtémoc', 'polanco', 'condesa', 'roma', 'del valle']
        exclude_terms = ['quintana roo', 'cancún', 'tulum', 'morelos', 'monterrey']
        
        has_cdmx = any(term in full_address for term in cdmx_terms)
        has_exclude = any(term in full_address for term in exclude_terms)
        
        return has_cdmx and not has_exclude

    def extract_from_page(self, url, listing_type, property_type):
        """Extract listings from page"""
        try:
            print(f"  {url}")
            response = self.session.get(url, timeout=20)
            
            if response.status_code != 200:
                print(f"    ⚠ Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script', type='application/ld+json')
            
            listings = []
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    
                    if data.get('@type') == 'Product':
                        if not self.is_cdmx(data.get('address', {})):
                            continue
                        
                        # Extract data
                        name = data.get('name', '')
                        price_data = data.get('offers', {})
                        price_mxn = None
                        
                        if isinstance(price_data, dict):
                            price_mxn = price_data.get('price')
                            if isinstance(price_mxn, str):
                                price_mxn = float(re.sub(r'[^\d.]', '', price_mxn))
                        
                        if not price_mxn or price_mxn == 0:
                            continue
                        
                        # Address
                        address_data = data.get('address', {})
                        city = address_data.get('addressRegion', 'Ciudad de México')
                        colonia = address_data.get('addressLocality', '')
                        
                        # Size - important for terrenos
                        size_m2 = None
                        lot_size_m2 = None
                        
                        # Try to extract from additionalProperty
                        props = data.get('additionalProperty', [])
                        for prop in props:
                            if isinstance(prop, dict):
                                prop_name = prop.get('name', '').lower()
                                prop_value = prop.get('value')
                                
                                if 'área' in prop_name or 'area' in prop_name:
                                    try:
                                        if 'terreno' in prop_name or 'lote' in prop_name:
                                            lot_size_m2 = float(re.sub(r'[^\d.]', '', str(prop_value)))
                                        else:
                                            size_m2 = float(re.sub(r'[^\d.]', '', str(prop_value)))
                                    except:
                                        pass
                        
                        # For terrenos, if we have size_m2 but not lot_size_m2, it's the lot
                        if property_type == 'terreno' and size_m2 and not lot_size_m2:
                            lot_size_m2 = size_m2
                            size_m2 = None
                        
                        # Calculate price per m²
                        price_per_m2 = None
                        if lot_size_m2:
                            price_per_m2 = price_mxn / lot_size_m2
                        elif size_m2:
                            price_per_m2 = price_mxn / size_m2
                        
                        # URL
                        url_data = data.get('url', '')
                        if url_data and not url_data.startswith('http'):
                            url_data = self.base_url + url_data
                        
                        # Source ID from URL
                        source_id = url_data.split('/')[-1] if url_data else None
                        
                        listing = {
                            'source': 'lamudi',
                            'source_id': source_id,
                            'url': url_data,
                            'title': name,
                            'price_mxn': price_mxn,
                            'property_type': property_type,
                            'listing_type': listing_type,
                            'size_m2': size_m2,
                            'lot_size_m2': lot_size_m2,
                            'city': city,
                            'colonia': colonia,
                            'images': [],  # Lamudi images require separate extraction
                            'raw_data': json.dumps({
                                'price_per_m2': price_per_m2
                            })
                        }
                        
                        listings.append(listing)
                        
                except Exception as e:
                    continue
            
            return listings
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return []

    def scrape_all(self):
        """Scrape all developer-focused properties"""
        urls = self.get_developer_urls()
        
        print(f"\n🏗️  LAMUDI DEVELOPER-FOCUSED SCRAPER")
        print(f"   Focus: TERRENOS + COMMERCIAL only")
        print(f"   Total URLs: {len(urls)}\n")
        
        all_listings = []
        terrenos_count = 0
        commercial_count = 0
        
        for i, (listing_type, prop_type, url) in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {prop_type.upper()}")
            
            listings = self.extract_from_page(url, listing_type, prop_type)
            
            for listing in listings:
                if listing['property_type'] == 'terreno':
                    terrenos_count += 1
                else:
                    commercial_count += 1
            
            all_listings.extend(listings)
            print(f"    ✓ +{len(listings)} | Total: {len(all_listings)} (T:{terrenos_count}, C:{commercial_count})\n")
            
            time.sleep(1.5)  # Be respectful
        
        return all_listings, terrenos_count, commercial_count

    def store_in_db(self, listings):
        """Store in database"""
        db = PolpiDB()
        stored = 0
        skipped = 0
        
        for listing in listings:
            try:
                db.insert_listing(listing)
                stored += 1
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    skipped += 1
        
        print(f"\n💾 Database: +{stored} new, ⊘ {skipped} duplicates")
        return stored

def main():
    try:
        # Initial stats
        db = PolpiDB()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM listings WHERE property_type = "terreno"')
        initial_terrenos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM listings WHERE property_type IN ("oficina", "local_comercial", "bodega", "edificio")')
        initial_commercial = cursor.fetchone()[0]
        
        conn.close()
        
        print("=" * 70)
        print(f"📊 INITIAL STATE")
        print(f"   Terrenos: {initial_terrenos}")
        print(f"   Commercial: {initial_commercial}")
        print("=" * 70)
        
        # Scrape
        scraper = LamudiDeveloperScraper()
        listings, terrenos_count, commercial_count = scraper.scrape_all()
        
        print("\n" + "=" * 70)
        print(f"📊 SCRAPED: {len(listings)} listings")
        print(f"   Terrenos: {terrenos_count}")
        print(f"   Commercial: {commercial_count}")
        print("=" * 70)
        
        if listings:
            # Show samples
            terrenos = [l for l in listings if l['property_type'] == 'terreno']
            if terrenos:
                print(f"\n🏞️  TERRENO SAMPLES:")
                for i, l in enumerate(terrenos[:3], 1):
                    price = f"${l.get('price_mxn'):,.0f}" if l.get('price_mxn') else "N/A"
                    lot = f"{l.get('lot_size_m2'):,.0f} m²" if l.get('lot_size_m2') else "N/A"
                    print(f"   {i}. {l.get('title', '')[:60]}")
                    print(f"      {price} | {lot}")
            
            # Store
            stored = scraper.store_in_db(listings)
        
        # Final stats
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM listings WHERE property_type = "terreno"')
        final_terrenos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM listings WHERE property_type IN ("oficina", "local_comercial", "bodega", "edificio")')
        final_commercial = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "=" * 70)
        print(f"🎯 FINAL STATE")
        print(f"   Terrenos: {final_terrenos} (+{final_terrenos - initial_terrenos})")
        print(f"   Commercial: {final_commercial} (+{final_commercial - initial_commercial})")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
