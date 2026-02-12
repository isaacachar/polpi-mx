#!/usr/bin/env python3
"""
Inmuebles24 scraper using pre-fetched HTML files
This works around Cloudflare protection by using browser automation to fetch HTML
"""

import sys
import json
import re
import hashlib
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB


def parse_inmuebles24_html(html_content, listing_type):
    """Parse Inmuebles24 HTML and extract listings"""
    soup = BeautifulSoup(html_content, 'html.parser')
    listings = []
    
    # Parse JSON-LD data first
    json_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            
            # Handle RealEstateListing with mainEntity
            if isinstance(data, dict) and data.get('@type') == 'RealEstateListing':
                main_entity = data.get('mainEntity', [])
                
                for entity in main_entity:
                    if entity.get('type') == 'RealEstateListing':
                        listing = {
                            'source': 'inmuebles24',
                            'listing_type': listing_type,
                            'title': entity.get('name', '').strip(),
                            'description': (entity.get('description', '') or '')[:500],
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
                        
                        # Parse price from description/name
                        text = (entity.get('name', '') + ' ' + entity.get('description', '')).upper()
                        price_match = re.search(r'MN\s*([\d,]+)', text)
                        if price_match:
                            try:
                                price_str = price_match.group(1).replace(',', '')
                                listing['price_mxn'] = float(price_str)
                            except:
                                listing['price_mxn'] = None
                        
                        # Parse bedrooms
                        bed_match = re.search(r'(\d+)\s*(recámara|recamara|rec\.|bedroom)', text, re.IGNORECASE)
                        if bed_match:
                            listing['bedrooms'] = int(bed_match.group(1))
                        else:
                            listing['bedrooms'] = None
                        
                        # Parse bathrooms
                        bath_match = re.search(r'(\d+)\s*(baño|bano|bathroom)', text, re.IGNORECASE)
                        if bath_match:
                            listing['bathrooms'] = int(bath_match.group(1))
                        else:
                            listing['bathrooms'] = None
                        
                        # Parse size
                        size_match = re.search(r'(\d+)\s*m²', text)
                        if size_match:
                            try:
                                listing['size_m2'] = float(size_match.group(1))
                            except:
                                listing['size_m2'] = None
                        
                        # Determine property type
                        title_lower = listing['title'].lower()
                        if 'casa' in title_lower:
                            listing['property_type'] = 'Casa'
                        elif 'departamento' in title_lower or 'depto' in title_lower:
                            listing['property_type'] = 'Departamento'
                        elif 'loft' in title_lower:
                            listing['property_type'] = 'Loft'
                        else:
                            listing['property_type'] = 'Departamento'
                        
                        if listing.get('url'):
                            listings.append(listing)
                        
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")
            continue
    
    return listings


def store_in_database(listings):
    """Store listings in database"""
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
                0,
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
    """Main function - parses pre-saved HTML files"""
    print("🏠 Inmuebles24 Parser (using saved HTML files)\n")
    
    # For now, just show we're ready to parse
    print("Ready to parse HTML files from data/html/ directory")
    print("\nTo use this scraper:")
    print("1. Use browser automation to save Inmuebles24 pages to data/html/")
    print("2. Name them: inmuebles24_sale_*.html or inmuebles24_rental_*.html")
    print("3. Run this script again")
    
    # Check if HTML files exist
    html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
    html_files = [f for f in os.listdir(html_dir) if f.startswith('inmuebles24_') and f.endswith('.html')]
    
    if html_files:
        print(f"\nFound {len(html_files)} Inmuebles24 HTML files")
        
        all_listings = []
        for html_file in html_files:
            # Determine type from filename
            listing_type = 'sale' if '_sale_' in html_file else 'rental'
            
            with open(os.path.join(html_dir, html_file), 'r', encoding='utf-8') as f:
                html_content = f.read()
                listings = parse_inmuebles24_html(html_content, listing_type)
                all_listings.extend(listings)
                print(f"  {html_file}: {len(listings)} listings")
        
        print(f"\nTotal listings parsed: {len(all_listings)}")
        
        if all_listings:
            stored = store_in_database(all_listings)
            print(f"💾 Stored {stored} listings in database")
            
            # Show samples
            print("\n🏠 Sample listings:")
            for i, listing in enumerate(all_listings[:5]):
                price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
                type_str = "SALE" if listing.get('listing_type') == 'sale' else "RENT"
                print(f"{i+1}. [{type_str}] {listing.get('title', '')[:60]}")
                print(f"   {price_str} | {listing.get('bedrooms', 'N/A')} bed | {listing.get('colonia', 'N/A')}")
    else:
        print("\nNo HTML files found yet.")


if __name__ == '__main__':
    main()
