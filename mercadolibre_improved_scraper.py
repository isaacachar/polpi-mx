#!/usr/bin/env python3
"""Improved MercadoLibre Scraper - Parses actual HTML structure"""

import sys
import json
import re
import hashlib
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class MercadoLibreImprovedScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        })
        self.base_url = 'https://inmuebles.mercadolibre.com.mx'

    def get_search_urls(self, pages_per_category=15):
        """Generate search URLs for CDMX properties"""
        urls = []
        
        categories = [
            ('/departamentos/venta/distrito-federal/', 'sale', 'departamento', pages_per_category),
            ('/casas/venta/distrito-federal/', 'sale', 'casa', pages_per_category),
            ('/departamentos/renta/distrito-federal/', 'rental', 'departamento', min(10, pages_per_category)),
            ('/casas/renta/distrito-federal/', 'rental', 'casa', min(10, pages_per_category)),
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

    def extract_listings_from_html(self, soup, listing_type, property_type):
        """Parse listings from the actual HTML structure"""
        listings = []
        
        # Find all listing items
        items = soup.find_all('li', class_=lambda x: x and 'ui-search-layout__item' in x if x else False)
        
        for item in items:
            try:
                listing = self.parse_listing_item(item, listing_type, property_type)
                if listing and listing.get('price_mxn'):
                    listings.append(listing)
            except Exception as e:
                continue
        
        return listings

    def parse_listing_item(self, item, listing_type, property_type):
        """Parse a single listing item"""
        listing = {
            'source': 'mercadolibre',
            'listing_type': listing_type,
            'property_type': property_type,
            'city': 'Ciudad de Mexico',
        }
        
        # Extract title and URL
        title_link = item.find('a', class_=lambda x: x and 'poly-component__title' in x if x else False)
        if not title_link:
            title_link = item.find('h3', class_='poly-component__title-wrapper')
            if title_link:
                title_link = title_link.find('a')
        
        if title_link:
            listing['title'] = title_link.get_text(strip=True)
            listing['url'] = title_link.get('href', '')
            
            # Extract source_id from URL
            url_match = re.search(r'MLM-?(\d+)', listing['url'])
            if url_match:
                listing['source_id'] = 'MLM-' + url_match.group(1)
            else:
                # Fallback: use a hash of the URL
                listing['source_id'] = 'ML_' + hashlib.md5(listing['url'].encode()).hexdigest()[:12]
        
        # Extract price
        price_elem = item.find('span', class_=lambda x: x and 'andes-money-amount__fraction' in x if x else False)
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Remove commas and convert
            price_text = price_text.replace(',', '').replace('.', '')
            try:
                listing['price_mxn'] = float(price_text)
            except:
                pass
        
        # Extract image
        img = item.find('img', class_=lambda x: x and 'poly-component__picture' in x if x else False)
        if img:
            img_url = img.get('src', '')
            if img_url:
                listing['images'] = [img_url]
        else:
            listing['images'] = []
        
        # Extract property attributes (bedrooms, bathrooms, size)
        attr_list = item.find('ul', class_='poly-attributes_list')
        if attr_list:
            attr_items = attr_list.find_all('li')
            for attr_item in attr_items:
                text = attr_item.get_text(strip=True).lower()
                
                # Bedrooms
                if 'recámara' in text or 'dormitorio' in text or 'cuarto' in text:
                    bed_match = re.search(r'(\d+)', text)
                    if bed_match:
                        listing['bedrooms'] = int(bed_match.group(1))
                
                # Bathrooms
                elif 'baño' in text:
                    bath_match = re.search(r'(\d+)', text)
                    if bath_match:
                        listing['bathrooms'] = int(bath_match.group(1))
                
                # Size
                elif 'm²' in text or 'm2' in text or 'construido' in text:
                    size_match = re.search(r'([\d,]+)', text.replace(',', ''))
                    if size_match:
                        try:
                            listing['size_m2'] = float(size_match.group(1))
                        except:
                            pass
        
        # Extract location
        location_elem = item.find('span', class_='poly-component__location')
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            # Try to extract colonia (usually the first part before comma)
            location_parts = location_text.split(',')
            if len(location_parts) >= 2:
                listing['colonia'] = location_parts[0].strip()
            else:
                listing['colonia'] = location_text[:50]
        
        # If we didn't get these fields, try to extract from title
        if not listing.get('bedrooms') or not listing.get('bathrooms') or not listing.get('size_m2'):
            self.extract_from_title(listing)
        
        return listing

    def extract_from_title(self, listing):
        """Extract bedrooms, bathrooms, size from title/description as fallback"""
        text = listing.get('title', '').lower()
        
        if not listing.get('bedrooms'):
            bed_match = re.search(r'(\d+)\s*(?:rec[aá]mara|habitaci[oó]n|dormitorio|bedroom)', text)
            if bed_match:
                listing['bedrooms'] = int(bed_match.group(1))
        
        if not listing.get('bathrooms'):
            bath_match = re.search(r'(\d+)\s*(?:ba[ñn]o|bathroom)', text)
            if bath_match:
                listing['bathrooms'] = int(bath_match.group(1))
        
        if not listing.get('size_m2'):
            size_match = re.search(r'(\d+)\s*m[²2]', text)
            if size_match:
                listing['size_m2'] = float(size_match.group(1))

    def scrape_page(self, search_info):
        """Scrape a single page"""
        url = search_info['url']
        listing_type = search_info['listing_type']
        property_type = search_info['property_type']
        
        try:
            print(f"  [{search_info['category']}] Page {search_info['page']}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            listings = self.extract_listings_from_html(soup, listing_type, property_type)
            
            print(f"    → Extracted {len(listings)} listings")
            return listings
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return []

    def scrape_all(self, pages_per_category=10, max_listings=500):
        """Scrape all categories"""
        urls = self.get_search_urls(pages_per_category)
        all_listings = []
        stats_by_category = {}
        
        print(f"\n🛒 MercadoLibre Improved Scraper")
        print(f"   Target: {len(urls)} pages across categories")
        print(f"   Goal: {max_listings}+ listings\n")
        
        for i, search_info in enumerate(urls):
            print(f"[{i+1}/{len(urls)}]", end=" ")
            
            listings = self.scrape_page(search_info)
            all_listings.extend(listings)
            
            # Track stats
            category = search_info['category']
            if category not in stats_by_category:
                stats_by_category[category] = 0
            stats_by_category[category] += len(listings)
            
            print(f"    Total: {len(all_listings)} listings")
            
            # Stop if we hit the goal
            if len(all_listings) >= max_listings:
                print(f"\n✓ Reached {max_listings}+ listings goal!")
                break
            
            # Rate limiting
            time.sleep(2)
        
        return all_listings, stats_by_category

    def store_in_database(self, listings):
        """Store listings in database"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate ID
                id_string = f"mercadolibre_{listing.get('source_id', '')}_{listing.get('url', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
                        id, source, source_id, url, title, price_mxn, bedrooms, bathrooms, size_m2,
                        city, colonia, images, scraped_date, listing_type, property_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    listing['source'],
                    listing.get('source_id', ''),
                    listing.get('url', ''),
                    listing.get('title', ''),
                    listing.get('price_mxn'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    listing.get('city', 'Ciudad de Mexico'),
                    listing.get('colonia', ''),
                    json.dumps(listing.get('images', [])),
                    datetime.now().isoformat(),
                    listing.get('listing_type', 'sale'),
                    listing.get('property_type', 'departamento')
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"  Error storing listing: {e}")
                continue
        
        return stored_count

def main():
    scraper = MercadoLibreImprovedScraper()
    
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
    
    # Scrape listings (increased pages to get more coverage)
    listings, stats_by_category = scraper.scrape_all(pages_per_category=15, max_listings=600)
    
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

if __name__ == '__main__':
    main()
