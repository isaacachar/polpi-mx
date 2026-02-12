#!/usr/bin/env python3
"""Inmuebles24 scraper for CDMX listings (sales and rentals)"""

import sys
import json
import re
import hashlib
import time
import cloudscraper
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class Inmuebles24Scraper:
    def __init__(self):
        # Use cloudscraper to bypass Cloudflare
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'mobile': False
            }
        )
        self.base_url = 'https://www.inmuebles24.com'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate search URLs for sales and rentals in CDMX"""
        urls = []
        
        # Sales - multiple pages
        sales_types = [
            ('/departamentos-en-venta-en-ciudad-de-mexico.html', 10),  # Apartments
            ('/casas-en-venta-en-ciudad-de-mexico.html', 8),           # Houses
        ]
        
        # Rentals - multiple pages
        rental_types = [
            ('/departamentos-en-renta-en-ciudad-de-mexico.html', 10),  # Apartments
            ('/casas-en-renta-en-ciudad-de-mexico.html', 8),           # Houses
        ]
        
        # Generate sale URLs
        for base_path, max_pages in sales_types:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append({
                        'url': self.base_url + base_path,
                        'type': 'sale'
                    })
                else:
                    urls.append({
                        'url': f"{self.base_url}{base_path}?pagina={page}",
                        'type': 'sale'
                    })
        
        # Generate rental URLs
        for base_path, max_pages in rental_types:
            for page in range(1, max_pages + 1):
                if page == 1:
                    urls.append({
                        'url': self.base_url + base_path,
                        'type': 'rental'
                    })
                else:
                    urls.append({
                        'url': f"{self.base_url}{base_path}?pagina={page}",
                        'type': 'rental'
                    })
        
        return urls

    def extract_listings_from_page(self, url, listing_type):
        """Extract listings from a single page"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save HTML for debugging
            filename = f"inmuebles24_{listing_type}_{int(time.time())}.html"
            with open(os.path.join(self.html_dir, filename), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse JSON-LD data
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            listings = []
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle RealEstateListing with mainEntity
                    if isinstance(data, dict) and data.get('@type') == 'RealEstateListing':
                        main_entity = data.get('mainEntity', [])
                        
                        for entity in main_entity:
                            if entity.get('type') == 'RealEstateListing':
                                listing = self.parse_json_listing(entity, listing_type)
                                if listing:
                                    listings.append(listing)
                    
                    # Handle individual Apartment entries
                    elif isinstance(data, dict) and data.get('@type') == 'Apartment':
                        # These are less detailed, we'll enhance from HTML
                        pass
                    
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    continue
            
            # Also extract from HTML for more complete data
            html_listings = self.parse_html_listings(soup, listing_type)
            
            # Merge JSON and HTML data
            all_listings = self.merge_listings(listings, html_listings)
            
            print(f"Extracted {len(all_listings)} listings from {url}")
            return all_listings
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []

    def parse_json_listing(self, entity, listing_type):
        """Parse a listing from JSON-LD data"""
        try:
            listing = {
                'source': 'inmuebles24',
                'listing_type': listing_type,
                'title': entity.get('name', '').strip(),
                'description': entity.get('description', '')[:500] if entity.get('description') else '',
                'url': entity.get('url', ''),
                'images': [],
                'colonia': '',
                'city': 'Ciudad de Mexico',
            }
            
            # Extract image
            image = entity.get('image')
            if image:
                if isinstance(image, str):
                    listing['images'] = [image]
                elif isinstance(image, list):
                    listing['images'] = image[:3]
            
            # Extract location from contentLocation
            content_location = entity.get('contentLocation', {})
            if isinstance(content_location, dict):
                place_name = content_location.get('name', '')
                if place_name:
                    listing['colonia'] = place_name
            
            # Extract price from description or name (often included)
            price_match = re.search(r'MN\s*([\d,]+)', entity.get('name', '') + ' ' + entity.get('description', ''))
            if price_match:
                try:
                    price_str = price_match.group(1).replace(',', '')
                    listing['price_mxn'] = float(price_str)
                except:
                    listing['price_mxn'] = None
            else:
                listing['price_mxn'] = None
            
            # Try to extract bedrooms/bathrooms from description
            bedrooms_match = re.search(r'(\d+)\s*(recámara|recamara|rec\.|bedroom)', entity.get('description', ''), re.IGNORECASE)
            if bedrooms_match:
                listing['bedrooms'] = int(bedrooms_match.group(1))
            else:
                listing['bedrooms'] = None
            
            bathrooms_match = re.search(r'(\d+)\s*(baño|bano|bathroom)', entity.get('description', ''), re.IGNORECASE)
            if bathrooms_match:
                listing['bathrooms'] = int(bathrooms_match.group(1))
            else:
                listing['bathrooms'] = None
            
            # Extract size
            size_match = re.search(r'(\d+)\s*m²', entity.get('name', '') + ' ' + entity.get('description', ''))
            if size_match:
                try:
                    listing['size_m2'] = float(size_match.group(1))
                except:
                    listing['size_m2'] = None
            else:
                listing['size_m2'] = None
            
            # Determine property type from title/description
            title_desc_lower = (entity.get('name', '') + ' ' + entity.get('description', '')).lower()
            if 'casa' in title_desc_lower:
                listing['property_type'] = 'Casa'
            elif 'departamento' in title_desc_lower or 'depto' in title_desc_lower:
                listing['property_type'] = 'Departamento'
            elif 'terreno' in title_desc_lower:
                listing['property_type'] = 'Terreno'
            elif 'loft' in title_desc_lower:
                listing['property_type'] = 'Loft'
            else:
                listing['property_type'] = 'Departamento'  # Default
            
            return listing
            
        except Exception as e:
            print(f"Error parsing JSON listing: {e}")
            return None

    def parse_html_listings(self, soup, listing_type):
        """Parse listings from HTML (for additional details)"""
        listings = []
        
        try:
            # Find listing cards - Inmuebles24 uses specific class names
            listing_cards = soup.find_all('div', class_=re.compile(r'posting-card|CardContainer'))
            
            for card in listing_cards:
                try:
                    listing = {
                        'source': 'inmuebles24',
                        'listing_type': listing_type,
                        'city': 'Ciudad de Mexico',
                    }
                    
                    # Extract title
                    title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=re.compile(r'title|Title'))
                    if title_elem:
                        listing['title'] = title_elem.get_text(strip=True)
                    else:
                        continue  # Skip if no title
                    
                    # Extract URL
                    url_elem = card.find('a', href=True)
                    if url_elem and url_elem['href']:
                        href = url_elem['href']
                        if href.startswith('/'):
                            listing['url'] = self.base_url + href
                        else:
                            listing['url'] = href
                    
                    # Extract price
                    price_elem = card.find(text=re.compile(r'MN\s*[\d,]+'))
                    if price_elem:
                        price_match = re.search(r'MN\s*([\d,]+)', price_elem)
                        if price_match:
                            try:
                                price_str = price_match.group(1).replace(',', '')
                                listing['price_mxn'] = float(price_str)
                            except:
                                listing['price_mxn'] = None
                    
                    # Extract location
                    location_elem = card.find(text=re.compile(r',\s*[A-Za-zá-úÁ-Ú\s]+,'))
                    if location_elem:
                        location_text = location_elem.strip()
                        parts = [p.strip() for p in location_text.split(',')]
                        if len(parts) >= 2:
                            listing['colonia'] = parts[0]
                    
                    # Extract attributes (bedrooms, bathrooms, size)
                    attr_text = card.get_text()
                    
                    # Bedrooms
                    bed_match = re.search(r'(\d+)\s*(Rec\.|recámara|bedroom)', attr_text, re.IGNORECASE)
                    if bed_match:
                        listing['bedrooms'] = int(bed_match.group(1))
                    
                    # Bathrooms
                    bath_match = re.search(r'(\d+)\s*(Baño|bathroom)', attr_text, re.IGNORECASE)
                    if bath_match:
                        listing['bathrooms'] = int(bath_match.group(1))
                    
                    # Size
                    size_match = re.search(r'(\d+)\s*m²', attr_text)
                    if size_match:
                        listing['size_m2'] = float(size_match.group(1))
                    
                    # Property type
                    if 'casa' in listing.get('title', '').lower():
                        listing['property_type'] = 'Casa'
                    elif 'departamento' in listing.get('title', '').lower():
                        listing['property_type'] = 'Departamento'
                    else:
                        listing['property_type'] = 'Departamento'
                    
                    # Extract image
                    img_elem = card.find('img', src=True)
                    if img_elem:
                        listing['images'] = [img_elem['src']]
                    else:
                        listing['images'] = []
                    
                    # Add description placeholder
                    listing['description'] = listing.get('title', '')[:200]
                    
                    if listing.get('url'):  # Must have URL
                        listings.append(listing)
                    
                except Exception as e:
                    print(f"Error parsing HTML card: {e}")
                    continue
        
        except Exception as e:
            print(f"Error parsing HTML listings: {e}")
        
        return listings

    def merge_listings(self, json_listings, html_listings):
        """Merge JSON and HTML data, preferring more complete information"""
        # Create a dict by URL for easy merging
        url_map = {}
        
        for listing in json_listings:
            url = listing.get('url')
            if url:
                url_map[url] = listing
        
        for listing in html_listings:
            url = listing.get('url')
            if url:
                if url in url_map:
                    # Merge: prefer non-None values
                    existing = url_map[url]
                    for key, value in listing.items():
                        if value and not existing.get(key):
                            existing[key] = value
                else:
                    url_map[url] = listing
        
        return list(url_map.values())

    def scrape_all_urls(self, max_listings=250):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        all_listings = []
        sales_count = 0
        rental_count = 0
        
        for i, url_info in enumerate(urls):
            url = url_info['url']
            listing_type = url_info['type']
            
            print(f"\nPage {i+1}/{len(urls)} ({listing_type})")
            
            listings = self.extract_listings_from_page(url, listing_type)
            all_listings.extend(listings)
            
            # Count by type
            for listing in listings:
                if listing.get('listing_type') == 'sale':
                    sales_count += 1
                else:
                    rental_count += 1
            
            # Progress update
            print(f"Total listings so far: {len(all_listings)} (Sales: {sales_count}, Rentals: {rental_count})")
            
            # Sleep between requests (respect rate limits)
            time.sleep(2)
            
            # Stop if we have enough listings
            if len(all_listings) >= max_listings:
                print(f"Reached target of {max_listings}+ listings ({len(all_listings)}), stopping")
                break
        
        return all_listings

    def store_in_database(self, listings):
        """Store listings in PolpiDB"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"inmuebles24_{listing.get('url', '')}_{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Extract source_id from URL
                source_id = None
                if listing.get('url'):
                    match = re.search(r'(\d+)\.html', listing['url'])
                    if match:
                        source_id = match.group(1)
                
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
                        id, source, source_id, url, title, price_mxn, property_type,
                        bedrooms, bathrooms, size_m2, city, colonia, description,
                        images, parking_spaces, scraped_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    listing['source'],
                    source_id,
                    listing.get('url', ''),
                    listing.get('title', ''),
                    listing.get('price_mxn'),
                    listing.get('property_type', 'Departamento'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    listing.get('city', 'Ciudad de Mexico'),
                    listing.get('colonia', ''),
                    listing.get('description', ''),
                    json.dumps(listing.get('images', [])),
                    0,  # parking_spaces
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing listing: {e}")
                continue
        
        return stored_count


def main():
    print("🏠 Starting Inmuebles24 CDMX scraper (Sales & Rentals)...")
    
    scraper = Inmuebles24Scraper()
    
    # Get current count
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "inmuebles24"')
    initial_count = cursor.fetchone()[0]
    conn.close()
    print(f"Starting with {initial_count} Inmuebles24 listings in database")
    
    # Scrape listings
    listings = scraper.scrape_all_urls(max_listings=250)
    
    print(f"\n📊 Scraped {len(listings)} listings total")
    
    # Count by type
    sales = [l for l in listings if l.get('listing_type') == 'sale']
    rentals = [l for l in listings if l.get('listing_type') == 'rental']
    print(f"   Sales: {len(sales)}")
    print(f"   Rentals: {len(rentals)}")
    
    if listings:
        # Store in database
        stored = scraper.store_in_database(listings)
        print(f"💾 Stored {stored} new listings in database")
        
        # Show sample listings
        print(f"\n🏠 Sample listings:")
        for i, listing in enumerate(listings[:5]):
            price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
            type_str = "SALE" if listing.get('listing_type') == 'sale' else "RENT"
            print(f"{i+1}. [{type_str}] {listing.get('title', 'No title')[:60]}")
            print(f"   {price_str} | {listing.get('size_m2', 'N/A')} m² | {listing.get('bedrooms', 'N/A')} bed | {listing.get('colonia', 'N/A')}")
    
    # Final count
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "inmuebles24"')
    final_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n🎯 Final count: {final_count} Inmuebles24 listings in database")
    print(f"Added {final_count - initial_count} new listings")
    
    if final_count >= 100:
        print("🎉 SUCCESS! Target achieved!")
    
    return final_count


if __name__ == '__main__':
    main()
