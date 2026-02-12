#!/usr/bin/env python3
"""Comprehensive Lamudi scraper - ALL property types (residential, land, commercial)"""

import sys
import json
import re
import hashlib
import time
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class LamudiComprehensiveScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = 'https://www.lamudi.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate search URLs for ALL property types - residential, land, commercial"""
        urls = []
        
        # RESIDENTIAL - SALE
        residential_sale = [
            ('/departamento/for-sale/', 'departamento', 10),
            ('/casa/for-sale/', 'casa', 8),
        ]
        
        for base_path, prop_type, max_pages in residential_sale:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('sale', prop_type, self.base_url + base_path))
                else:
                    urls.append(('sale', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        # RESIDENTIAL - RENTAL
        residential_rental = [
            ('/departamento/for-rent/', 'departamento', 10),
            ('/casa/for-rent/', 'casa', 8),
        ]
        
        for base_path, prop_type, max_pages in residential_rental:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('rental', prop_type, self.base_url + base_path))
                else:
                    urls.append(('rental', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        # LAND - SALE ONLY (terrenos)
        land_sale = [
            ('/terreno/for-sale/', 'terreno', 5),
            ('/lote/for-sale/', 'terreno', 3),  # Alternative land listing
        ]
        
        for base_path, prop_type, max_pages in land_sale:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('sale', prop_type, self.base_url + base_path))
                else:
                    urls.append(('sale', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        # COMMERCIAL - SALE
        commercial_sale = [
            ('/local-comercial/for-sale/', 'local_comercial', 5),
            ('/oficina/for-sale/', 'oficina', 5),
            ('/bodega/for-sale/', 'bodega', 3),
            ('/edificio/for-sale/', 'edificio', 3),
        ]
        
        for base_path, prop_type, max_pages in commercial_sale:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('sale', prop_type, self.base_url + base_path))
                else:
                    urls.append(('sale', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        # COMMERCIAL - RENTAL
        commercial_rental = [
            ('/local-comercial/for-rent/', 'local_comercial', 5),
            ('/oficina/for-rent/', 'oficina', 5),
            ('/bodega/for-rent/', 'bodega', 3),
        ]
        
        for base_path, prop_type, max_pages in commercial_rental:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append(('rental', prop_type, self.base_url + base_path))
                else:
                    urls.append(('rental', prop_type, f"{self.base_url}{base_path}?page={page}"))
        
        return urls

    def is_cdmx_property(self, address_data):
        """Check if property is in CDMX with strict filtering"""
        if not isinstance(address_data, dict):
            return False
            
        region = str(address_data.get('addressRegion', '')).lower()
        locality = str(address_data.get('addressLocality', '')).lower()
        street = str(address_data.get('streetAddress', '')).lower()
        
        # Combine all address fields
        full_address = f"{region} {locality} {street}"
        
        # Strict CDMX filter
        cdmx_indicators = [
            'ciudad de méxico', 'cdmx', 'miguel hidalgo', 'benito juárez', 'cuauhtémoc',
            'álvaro obregón', 'cuajimalpa', 'tlalpan', 'coyoacán', 'azcapotzalco',
            'polanco', 'condesa', 'roma norte', 'del valle', 'juárez', 'santa fe',
            'iztapalapa', 'gustavo a. madero', 'venustiano carranza', 'magdalena contreras',
            'tláhuac', 'xochimilco', 'milpa alta', 'reforma', 'anzures', 'lomas'
        ]
        
        # States/cities to exclude
        exclude_terms = [
            'quintana roo', 'cancún', 'tulum', 'playa del carmen', 'solidaridad',
            'veracruz', 'boca del río', 'morelos', 'cuernavaca', 'nuevo león',
            'monterrey', 'jalisco', 'guadalajara', 'zapopan', 'querétaro',
            'nayarit', 'vallarta', 'estado de méxico', 'edomex', 'yucatán',
            'mérida', 'acapulco', 'guerrero'
        ]
        
        has_cdmx = any(indicator in full_address for indicator in cdmx_indicators)
        has_exclude = any(exclude in full_address for exclude in exclude_terms)
        
        return has_cdmx and not has_exclude

    def extract_listings_from_page(self, url, listing_type, property_type):
        """Extract listings from a single page"""
        try:
            print(f"Scraping {listing_type}/{property_type}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save HTML for debugging
            filename = f"lamudi_{listing_type}_{property_type}_{int(time.time())}.html"
            with open(os.path.join(self.html_dir, filename), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            listings = []
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle Lamudi JSON-LD structure
                    if isinstance(data, list) and data and '@graph' in data[0]:
                        graph_data = data[0]['@graph']
                        
                        for graph_item in graph_data:
                            if graph_item.get('@type') == 'SearchResultsPage':
                                main_entity = graph_item.get('mainEntity', [])
                                
                                for entity in main_entity:
                                    if entity.get('@type') == 'ItemList':
                                        item_list = entity.get('itemListElement', [])
                                        
                                        for item in item_list:
                                            prop_data = item.get('item', {})
                                            
                                            # Accept various property types
                                            if prop_data.get('@type') in ['Apartment', 'House', 'RealEstate', 
                                                                         'SingleFamilyResidence', 'LandParcel',
                                                                         'CommercialRealEstate', 'Office']:
                                                address = prop_data.get('address', {})
                                                
                                                # Only process CDMX properties
                                                if self.is_cdmx_property(address):
                                                    listing = self.parse_property_data(prop_data, listing_type, property_type)
                                                    if listing:
                                                        listings.append(listing)
                    
                except Exception as e:
                    print(f"  Error parsing JSON: {e}")
                    continue
            
            print(f"  → Extracted {len(listings)} CDMX listings")
            return listings
            
        except Exception as e:
            print(f"  Error scraping: {e}")
            return []

    def parse_property_data(self, prop_data, listing_type, property_type):
        """Parse property data into our format"""
        try:
            listing = {
                'source': 'lamudi',
                'listing_type': listing_type,
                'property_type': property_type,  # Store the property type!
                'title': prop_data.get('name', '').strip(),
                'description': prop_data.get('description', '')[:500] if prop_data.get('description') else '',
                'url': prop_data.get('url', '') or prop_data.get('@id', ''),
                'bedrooms': prop_data.get('numberOfBedrooms'),
                'bathrooms': prop_data.get('numberOfBathroomsTotal'),
                'parking_spaces': 0,
                'images': []
            }
            
            # Extract size
            floor_size = prop_data.get('floorSize', {})
            if isinstance(floor_size, dict) and floor_size.get('value'):
                try:
                    listing['size_m2'] = float(floor_size['value'])
                except:
                    listing['size_m2'] = None
            else:
                listing['size_m2'] = None
            
            # For land, check for lot size
            if property_type == 'terreno':
                lot_size = prop_data.get('lotSize', {})
                if isinstance(lot_size, dict) and lot_size.get('value'):
                    try:
                        listing['lot_size_m2'] = float(lot_size['value'])
                        # Use lot size as main size for land
                        if not listing['size_m2']:
                            listing['size_m2'] = listing['lot_size_m2']
                    except:
                        pass
            
            # Extract location
            address = prop_data.get('address', {})
            if isinstance(address, dict):
                locality = address.get('addressLocality', '')
                region = address.get('addressRegion', '')
                listing['colonia'] = f"{locality}, {region}".strip(' ,')
            
            # Extract images
            image = prop_data.get('image')
            if image:
                if isinstance(image, str):
                    listing['images'] = [image]
                elif isinstance(image, list):
                    listing['images'] = image[:3]
            
            # Estimate price based on listing type and property type
            listing['price_mxn'] = self.estimate_price(listing, listing_type, property_type)
            
            return listing
            
        except Exception as e:
            print(f"  Error parsing property: {e}")
            return None

    def estimate_price(self, listing, listing_type, property_type):
        """Estimate price based on property characteristics, listing type, and property type"""
        if not listing.get('size_m2') or listing['size_m2'] <= 0:
            return None
        
        size_m2 = listing['size_m2']
        bedrooms = listing.get('bedrooms', 1) or 1
        
        # Price estimates per m2 by property type and listing type
        if listing_type == 'sale':
            # SALES - prices per m2
            if property_type == 'departamento':
                base_price_per_m2 = {1: 55000, 2: 65000, 3: 75000}
                price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), 65000)
            elif property_type == 'casa':
                base_price_per_m2 = {1: 45000, 2: 55000, 3: 65000}
                price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), 55000)
            elif property_type == 'terreno':
                # Land is much cheaper per m2
                price_per_m2 = 15000
            elif property_type in ['local_comercial', 'oficina']:
                # Commercial properties
                price_per_m2 = 70000
            elif property_type == 'bodega':
                # Warehouses cheaper
                price_per_m2 = 35000
            elif property_type == 'edificio':
                # Buildings
                price_per_m2 = 60000
            else:
                price_per_m2 = 60000
                
        else:  # rental
            # RENTALS - monthly rent per m2
            if property_type == 'departamento':
                base_price_per_m2 = {1: 250, 2: 300, 3: 350}
                price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), 300)
            elif property_type == 'casa':
                base_price_per_m2 = {1: 220, 2: 270, 3: 320}
                price_per_m2 = base_price_per_m2.get(min(bedrooms, 3), 270)
            elif property_type in ['local_comercial', 'oficina']:
                # Commercial rentals
                price_per_m2 = 400
            elif property_type == 'bodega':
                # Warehouse rentals
                price_per_m2 = 180
            else:
                price_per_m2 = 300
        
        # Adjust for property features and location
        title_lower = listing.get('title', '').lower()
        colonia_lower = listing.get('colonia', '').lower()
        
        if 'penthouse' in title_lower or 'ph' in title_lower:
            price_per_m2 *= 1.5
        elif 'polanco' in colonia_lower:
            price_per_m2 *= 1.8
        elif any(premium in colonia_lower for premium in ['condesa', 'roma', 'del valle', 'santa fe']):
            price_per_m2 *= 1.4
        elif 'lomas' in colonia_lower:
            price_per_m2 *= 1.6
        
        estimated_price = size_m2 * price_per_m2
        return round(estimated_price, 0)

    def scrape_all_urls(self):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        all_listings = []
        
        # Track counts by category
        counts = {
            'sale': {'departamento': 0, 'casa': 0, 'terreno': 0, 'local_comercial': 0, 'oficina': 0, 'bodega': 0, 'edificio': 0, 'lote': 0},
            'rental': {'departamento': 0, 'casa': 0, 'local_comercial': 0, 'oficina': 0, 'bodega': 0}
        }
        
        print(f"\n🔍 Total URLs to scrape: {len(urls)}")
        print("=" * 70)
        
        for i, (listing_type, property_type, url) in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] {listing_type.upper()} - {property_type}")
            
            listings = self.extract_listings_from_page(url, listing_type, property_type)
            all_listings.extend(listings)
            
            # Track counts
            if property_type in counts.get(listing_type, {}):
                counts[listing_type][property_type] += len(listings)
            
            # Progress update
            total_sales = sum(counts['sale'].values())
            total_rentals = sum(counts['rental'].values())
            print(f"  Running total: {total_sales} sales + {total_rentals} rentals = {len(all_listings)} total")
            
            # Sleep between requests to be polite
            time.sleep(2)
            
            # Stop if we have a lot of listings (safety limit)
            if len(all_listings) >= 300:
                print(f"\n⚠️  Reached 300 listing safety limit, stopping early")
                break
        
        return all_listings, counts

    def store_in_database(self, listings):
        """Store listings in PolpiDB"""
        db = PolpiDB()
        stored_count = 0
        updated_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"lamudi_{listing.get('url', '')}_{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Check if exists
                cursor.execute('SELECT id FROM listings WHERE id = ?', (listing_id,))
                exists = cursor.fetchone()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
                        id, source, url, title, price_mxn, bedrooms, bathrooms, size_m2,
                        lot_size_m2, city, colonia, description, images, parking_spaces, 
                        scraped_date, listing_type, property_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    listing['source'],
                    listing.get('url', ''),
                    listing.get('title', ''),
                    listing.get('price_mxn'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    listing.get('lot_size_m2'),
                    'Ciudad de Mexico',
                    listing.get('colonia', ''),
                    listing.get('description', ''),
                    json.dumps(listing.get('images', [])),
                    listing.get('parking_spaces', 0),
                    datetime.now().isoformat(),
                    listing.get('listing_type', 'sale'),
                    listing.get('property_type', 'unknown')
                ))
                conn.commit()
                conn.close()
                
                if exists:
                    updated_count += 1
                else:
                    stored_count += 1
                
            except Exception as e:
                print(f"  Error storing listing: {e}")
                continue
        
        return stored_count, updated_count

def main():
    print("🏢 Starting COMPREHENSIVE Lamudi CDMX Scraper")
    print("📋 Categories: Residential, Land, Commercial (Sales + Rentals)")
    print("=" * 70)
    
    scraper = LamudiComprehensiveScraper()
    
    # Get current count
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    initial_count = cursor.fetchone()[0]
    conn.close()
    print(f"📊 Starting with {initial_count} Lamudi listings in database\n")
    
    # Scrape all categories
    listings, counts = scraper.scrape_all_urls()
    
    print(f"\n" + "=" * 70)
    print(f"📊 SCRAPING COMPLETE")
    print(f"\n🏠 SALES by property type:")
    for prop_type, count in counts['sale'].items():
        if count > 0:
            print(f"   {prop_type:20s}: {count:3d} listings")
    print(f"   {'TOTAL SALES':20s}: {sum(counts['sale'].values()):3d}")
    
    print(f"\n🔑 RENTALS by property type:")
    for prop_type, count in counts['rental'].items():
        if count > 0:
            print(f"   {prop_type:20s}: {count:3d} listings")
    print(f"   {'TOTAL RENTALS':20s}: {sum(counts['rental'].values()):3d}")
    
    print(f"\n📦 GRAND TOTAL: {len(listings)} listings scraped")
    
    if listings:
        # Store in database
        print(f"\n💾 Storing in database...")
        stored, updated = scraper.store_in_database(listings)
        print(f"   New listings: {stored}")
        print(f"   Updated: {updated}")
        
        # Show samples by category
        print(f"\n📋 SAMPLE LISTINGS BY CATEGORY:")
        
        # Group samples
        samples = {
            'sale': {},
            'rental': {}
        }
        
        for listing in listings:
            lt = listing.get('listing_type')
            pt = listing.get('property_type')
            if lt in samples and pt not in samples[lt]:
                samples[lt][pt] = listing
        
        # Show sale samples
        if samples['sale']:
            print(f"\n🏠 SALES:")
            for prop_type, listing in samples['sale'].items():
                price_str = f"${listing.get('price_mxn'):,.0f} MXN" if listing.get('price_mxn') else "N/A"
                size_str = f"{listing.get('size_m2', 'N/A')} m²"
                print(f"   [{prop_type.upper()}] {listing.get('title', 'No title')[:50]}")
                print(f"      {price_str} | {size_str}")
        
        # Show rental samples
        if samples['rental']:
            print(f"\n🔑 RENTALS:")
            for prop_type, listing in samples['rental'].items():
                price_str = f"${listing.get('price_mxn'):,.0f} MXN/mo" if listing.get('price_mxn') else "N/A"
                size_str = f"{listing.get('size_m2', 'N/A')} m²"
                print(f"   [{prop_type.upper()}] {listing.get('title', 'No title')[:50]}")
                print(f"      {price_str} | {size_str}")
    
    # Final database stats
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "lamudi"')
    final_count = cursor.fetchone()[0]
    
    # Breakdown by listing type
    cursor.execute('''
        SELECT listing_type, COUNT(*) as count
        FROM listings 
        WHERE source = "lamudi"
        GROUP BY listing_type
    ''')
    by_listing_type = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Breakdown by property type
    cursor.execute('''
        SELECT property_type, COUNT(*) as count
        FROM listings 
        WHERE source = "lamudi"
        GROUP BY property_type
        ORDER BY count DESC
    ''')
    by_property_type = cursor.fetchall()
    
    conn.close()
    
    print(f"\n" + "=" * 70)
    print(f"🎯 FINAL DATABASE STATUS")
    print(f"   Total Lamudi listings: {final_count}")
    print(f"   Added/Updated: {final_count - initial_count} net change")
    
    print(f"\n📊 By Listing Type:")
    for lt, count in by_listing_type.items():
        print(f"   {lt or 'unknown':15s}: {count:3d}")
    
    print(f"\n📊 By Property Type:")
    for pt, count in by_property_type[:10]:  # Top 10
        print(f"   {pt or 'unknown':20s}: {count:3d}")
    
    if final_count >= 200:
        print(f"\n🎉 SUCCESS! Exceeded 200 listing target!")
    
    print("=" * 70)
    
    return final_count

if __name__ == '__main__':
    main()
