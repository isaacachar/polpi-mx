#!/usr/bin/env python3
"""Vivanuncios scraper for Polpi MX - CDMX listings (sales, rentals, land, commercial)"""

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

class VivanunciosScraper:
    def __init__(self):
        # Use cloudscraper to bypass Cloudflare/protection
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'mobile': False
            }
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.vivanuncios.com.mx/',
        })
        self.base_url = 'https://www.vivanuncios.com.mx'
        self.html_dir = '/Users/isaachomefolder/Desktop/polpi-mx/data/html'
        os.makedirs(self.html_dir, exist_ok=True)

    def get_search_urls(self):
        """Generate search URLs for different property types in CDMX"""
        urls = []
        
        # SALES URLs - distrito-federal = CDMX (code l1008)
        # v1c1097 = venta inmuebles category
        sales_searches = [
            # Residential sales
            ('/s-inmuebles/cdmx/v1c1097l13116p', 'sale', 'residential', 5),  # All CDMX properties
            ('/s-casas/cdmx/v1c1020l13116p', 'sale', 'casa', 3),  # Houses
            ('/s-departamento-piso/cdmx/v1c1019l13116p', 'sale', 'departamento', 5),  # Apartments
            # Land
            ('/s-terrenos/cdmx/v1c1025l13116p', 'sale', 'terreno', 2),  # Land
            # Commercial
            ('/s-locales-oficinas/cdmx/v1c1021l13116p', 'sale', 'comercial', 2),  # Commercial
        ]
        
        # RENTAL URLs
        # v1c1098 = renta inmuebles category
        rental_searches = [
            # Residential rentals
            ('/s-inmuebles/cdmx/v1c1098l13116p', 'rental', 'residential', 5),  # All CDMX rentals
            ('/s-casas/cdmx/v1c1029l13116p', 'rental', 'casa', 3),  # Houses for rent
            ('/s-departamento-piso/cdmx/v1c1028l13116p', 'rental', 'departamento', 5),  # Apartments for rent
            # Commercial rentals
            ('/s-locales-oficinas/cdmx/v1c1030l13116p', 'rental', 'comercial', 2),  # Commercial for rent
        ]
        
        # Generate URLs with pagination
        for base_path, listing_type, property_category, max_pages in sales_searches + rental_searches:
            for page in range(1, max_pages + 1):
                urls.append({
                    'url': f"{self.base_url}{base_path}{page}",
                    'listing_type': listing_type,
                    'property_category': property_category
                })
        
        return urls

    def extract_listings_from_page(self, url_info):
        """Extract listings from a single page"""
        url = url_info['url']
        listing_type = url_info['listing_type']
        property_category = url_info['property_category']
        
        try:
            print(f"Scraping {listing_type}/{property_category}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for captcha/block
            if 'captcha' in response.text.lower() or 'just a moment' in response.text.lower():
                print("⚠️ Blocked by anti-bot protection (captcha)")
                return []
            
            # Save HTML for debugging
            filename = f"vivanuncios_{listing_type}_{property_category}_{int(time.time())}.html"
            with open(os.path.join(self.html_dir, filename), 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple parsing strategies
            listings = []
            
            # Strategy 1: JSON-LD structured data
            json_listings = self.parse_json_ld(soup, listing_type, property_category)
            listings.extend(json_listings)
            
            # Strategy 2: HTML parsing
            html_listings = self.parse_html_listings(soup, listing_type, property_category)
            listings.extend(html_listings)
            
            # Deduplicate by URL
            seen_urls = set()
            unique_listings = []
            for listing in listings:
                url = listing.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_listings.append(listing)
            
            print(f"  → Extracted {len(unique_listings)} listings")
            return unique_listings
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return []

    def parse_json_ld(self, soup, listing_type, property_category):
        """Parse listings from JSON-LD structured data"""
        listings = []
        
        try:
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle different JSON-LD structures
                    if isinstance(data, dict):
                        # Single listing
                        if data.get('@type') in ['Product', 'Offer', 'RealEstateListing']:
                            listing = self.parse_json_listing(data, listing_type, property_category)
                            if listing:
                                listings.append(listing)
                        
                        # ItemList with multiple listings
                        elif data.get('@type') == 'ItemList':
                            items = data.get('itemListElement', [])
                            for item in items:
                                item_data = item.get('item', {}) if isinstance(item, dict) else item
                                listing = self.parse_json_listing(item_data, listing_type, property_category)
                                if listing:
                                    listings.append(listing)
                    
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') in ['Product', 'Offer', 'RealEstateListing']:
                                listing = self.parse_json_listing(item, listing_type, property_category)
                                if listing:
                                    listings.append(listing)
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"  Error parsing JSON-LD: {e}")
                    continue
        
        except Exception as e:
            print(f"  Error in JSON-LD parsing: {e}")
        
        return listings

    def parse_json_listing(self, data, listing_type, property_category):
        """Parse a single listing from JSON data"""
        try:
            listing = {
                'source': 'vivanuncios',
                'listing_type': listing_type,
                'city': 'Ciudad de Mexico',
            }
            
            # Extract title/name
            listing['title'] = data.get('name', '').strip()
            if not listing['title']:
                return None
            
            # Extract URL
            listing['url'] = data.get('url', '') or data.get('@id', '')
            if listing['url'] and not listing['url'].startswith('http'):
                listing['url'] = self.base_url + listing['url']
            
            # Extract description
            listing['description'] = (data.get('description', '') or '')[:500]
            
            # Extract price
            if 'offers' in data:
                offers = data['offers']
                if isinstance(offers, dict):
                    price = offers.get('price') or offers.get('lowPrice')
                    if price:
                        try:
                            listing['price_mxn'] = float(str(price).replace(',', ''))
                        except:
                            listing['price_mxn'] = None
            
            # Extract images
            images = data.get('image', [])
            if isinstance(images, str):
                listing['images'] = [images]
            elif isinstance(images, list):
                listing['images'] = images[:5]
            else:
                listing['images'] = []
            
            # Extract location
            if 'address' in data:
                address = data['address']
                if isinstance(address, dict):
                    listing['colonia'] = address.get('addressLocality', '') or address.get('streetAddress', '')
                elif isinstance(address, str):
                    listing['colonia'] = address
            
            # Determine property type from category and title
            listing['property_type'] = self.determine_property_type(
                listing['title'], 
                listing.get('description', ''),
                property_category
            )
            
            # Extract attributes from description/title
            self.extract_attributes(listing)
            
            return listing
            
        except Exception as e:
            print(f"  Error parsing JSON listing: {e}")
            return None

    def parse_html_listings(self, soup, listing_type, property_category):
        """Parse listings from HTML structure"""
        listings = []
        
        try:
            # Vivanuncios uses various class names - try multiple patterns
            card_selectors = [
                'div[class*="tileV1"]',
                'div[class*="listing"]',
                'div[class*="result"]',
                'article[class*="item"]',
                'div[data-ad-id]',
            ]
            
            cards = []
            for selector in card_selectors:
                cards = soup.select(selector)
                if cards:
                    break
            
            if not cards:
                # Try finding by common patterns
                cards = soup.find_all('div', class_=re.compile(r'tile|listing|result|item'))
            
            for card in cards:
                try:
                    listing = {
                        'source': 'vivanuncios',
                        'listing_type': listing_type,
                        'city': 'Ciudad de Mexico',
                    }
                    
                    # Extract title
                    title_elem = (
                        card.find('h2') or 
                        card.find('h3') or 
                        card.find('a', class_=re.compile(r'title|heading'))
                    )
                    if title_elem:
                        listing['title'] = title_elem.get_text(strip=True)
                    else:
                        continue  # Skip if no title
                    
                    # Extract URL
                    url_elem = card.find('a', href=True)
                    if url_elem:
                        href = url_elem['href']
                        if href.startswith('/'):
                            listing['url'] = self.base_url + href
                        elif href.startswith('http'):
                            listing['url'] = href
                        else:
                            listing['url'] = self.base_url + '/' + href
                    else:
                        continue  # Skip if no URL
                    
                    # Extract price
                    price_elem = card.find(text=re.compile(r'\$[\d,]+'))
                    if price_elem:
                        price_match = re.search(r'\$([\d,]+)', price_elem)
                        if price_match:
                            try:
                                price_str = price_match.group(1).replace(',', '')
                                listing['price_mxn'] = float(price_str)
                            except:
                                listing['price_mxn'] = None
                    
                    # Extract location
                    location_elem = card.find(text=re.compile(r',\s*[A-Za-zá-úÁ-Ú\s]+'))
                    if location_elem:
                        # Parse location string
                        location_parts = [p.strip() for p in str(location_elem).split(',')]
                        if location_parts:
                            listing['colonia'] = location_parts[0]
                    
                    # Extract image
                    img_elem = card.find('img', src=True)
                    if img_elem:
                        listing['images'] = [img_elem['src']]
                    else:
                        listing['images'] = []
                    
                    # Get all text for attribute extraction
                    card_text = card.get_text()
                    
                    # Extract attributes
                    listing['property_type'] = self.determine_property_type(
                        listing['title'], 
                        card_text,
                        property_category
                    )
                    
                    # Extract bedrooms
                    bed_match = re.search(r'(\d+)\s*(rec[aáâ]?m[aá]?|bedroom|hab|cuarto)', card_text, re.IGNORECASE)
                    if bed_match:
                        listing['bedrooms'] = int(bed_match.group(1))
                    else:
                        listing['bedrooms'] = None
                    
                    # Extract bathrooms
                    bath_match = re.search(r'(\d+)\s*(ba[ñn]o|bathroom)', card_text, re.IGNORECASE)
                    if bath_match:
                        listing['bathrooms'] = int(bath_match.group(1))
                    else:
                        listing['bathrooms'] = None
                    
                    # Extract size
                    size_match = re.search(r'(\d+)\s*m[²2]', card_text)
                    if size_match:
                        listing['size_m2'] = float(size_match.group(1))
                    else:
                        listing['size_m2'] = None
                    
                    # Description
                    listing['description'] = listing['title'][:200]
                    
                    if listing.get('url'):
                        listings.append(listing)
                
                except Exception as e:
                    print(f"  Error parsing HTML card: {e}")
                    continue
        
        except Exception as e:
            print(f"  Error in HTML parsing: {e}")
        
        return listings

    def determine_property_type(self, title, description, category_hint):
        """Determine property type from text and category"""
        text = (title + ' ' + description).lower()
        
        # Check category hint first
        if category_hint == 'terreno':
            return 'terreno'
        elif category_hint == 'comercial':
            # Differentiate between local and oficina
            if 'oficina' in text or 'office' in text:
                return 'oficina'
            else:
                return 'local_comercial'
        
        # Check text for property type keywords
        if 'terreno' in text or 'land' in text:
            return 'terreno'
        elif 'local' in text or 'comercial' in text:
            return 'local_comercial'
        elif 'oficina' in text or 'office' in text:
            return 'oficina'
        elif 'casa' in text or 'house' in text:
            return 'casa'
        elif 'departamento' in text or 'depto' in text or 'apartment' in text:
            return 'departamento'
        elif 'penthouse' in text or 'pent house' in text:
            return 'departamento'  # Penthouse is a type of apartment
        
        # Default based on category hint
        if category_hint == 'casa':
            return 'casa'
        elif category_hint == 'departamento':
            return 'departamento'
        
        return 'departamento'  # Default fallback

    def extract_attributes(self, listing):
        """Extract bedrooms, bathrooms, size from title/description"""
        text = listing.get('title', '') + ' ' + listing.get('description', '')
        
        # Bedrooms
        if 'bedrooms' not in listing or not listing.get('bedrooms'):
            bed_match = re.search(r'(\d+)\s*(rec[aáâ]?m[aá]?|bedroom|hab|cuarto)', text, re.IGNORECASE)
            if bed_match:
                listing['bedrooms'] = int(bed_match.group(1))
            else:
                listing['bedrooms'] = None
        
        # Bathrooms
        if 'bathrooms' not in listing or not listing.get('bathrooms'):
            bath_match = re.search(r'(\d+)\s*(ba[ñn]o|bathroom)', text, re.IGNORECASE)
            if bath_match:
                listing['bathrooms'] = int(bath_match.group(1))
            else:
                listing['bathrooms'] = None
        
        # Size
        if 'size_m2' not in listing or not listing.get('size_m2'):
            size_match = re.search(r'(\d+)\s*m[²2]', text)
            if size_match:
                listing['size_m2'] = float(size_match.group(1))
            else:
                listing['size_m2'] = None

    def scrape_all_urls(self, test_mode=False):
        """Scrape all URLs and collect listings"""
        urls = self.get_search_urls()
        
        # If test mode, only scrape first 3 pages
        if test_mode:
            urls = urls[:3]
            print(f"🧪 TEST MODE: Scraping only {len(urls)} pages\n")
        
        all_listings = []
        stats = {
            'sale': {'residential': 0, 'terreno': 0, 'comercial': 0},
            'rental': {'residential': 0, 'comercial': 0}
        }
        
        for i, url_info in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}]")
            
            listings = self.extract_listings_from_page(url_info)
            
            # Update stats
            listing_type = url_info['listing_type']
            for listing in listings:
                prop_type = listing.get('property_type', '')
                if prop_type in ['terreno']:
                    stats[listing_type]['terreno'] = stats[listing_type].get('terreno', 0) + 1
                elif prop_type in ['local_comercial', 'oficina']:
                    stats[listing_type]['comercial'] = stats[listing_type].get('comercial', 0) + 1
                else:
                    stats[listing_type]['residential'] = stats[listing_type].get('residential', 0) + 1
            
            all_listings.extend(listings)
            
            # Progress update
            print(f"Total listings: {len(all_listings)}")
            print(f"  Sales: {sum(stats['sale'].values())} (res: {stats['sale']['residential']}, land: {stats['sale'].get('terreno', 0)}, com: {stats['sale']['comercial']})")
            print(f"  Rentals: {sum(stats['rental'].values())} (res: {stats['rental']['residential']}, com: {stats['rental']['comercial']})")
            
            # Sleep to respect rate limits
            time.sleep(2)
            
            # Stop if we have enough listings and not in test mode
            if not test_mode and len(all_listings) >= 200:
                print(f"\n🎯 Reached target of 200+ listings ({len(all_listings)}), stopping")
                break
        
        return all_listings, stats

    def store_in_database(self, listings):
        """Store listings in PolpiDB"""
        db = PolpiDB()
        stored_count = 0
        
        for listing in listings:
            try:
                # Generate unique ID
                id_string = f"vivanuncios_{listing.get('url', '')}_{listing.get('title', '')}"
                listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                # Extract source_id from URL (ad ID)
                source_id = None
                if listing.get('url'):
                    # Vivanuncios URLs often have format: /a-category/location/title.ID-adID
                    match = re.search(r'\.(\d+)-(\d+)$', listing['url'].rstrip('/'))
                    if match:
                        source_id = match.group(2)
                    else:
                        # Alternative pattern
                        match = re.search(r'/(\d+)$', listing['url'].rstrip('/'))
                        if match:
                            source_id = match.group(1)
                
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO listings (
                        id, source, source_id, url, title, price_mxn, property_type,
                        bedrooms, bathrooms, size_m2, city, colonia, description,
                        images, parking_spaces, scraped_date, listing_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing_id,
                    listing['source'],
                    source_id,
                    listing.get('url', ''),
                    listing.get('title', ''),
                    listing.get('price_mxn'),
                    listing.get('property_type', 'departamento'),
                    listing.get('bedrooms'),
                    listing.get('bathrooms'),
                    listing.get('size_m2'),
                    listing.get('city', 'Ciudad de Mexico'),
                    listing.get('colonia', ''),
                    listing.get('description', ''),
                    json.dumps(listing.get('images', [])),
                    0,  # parking_spaces
                    datetime.now().isoformat(),
                    listing.get('listing_type', 'sale')
                ))
                conn.commit()
                conn.close()
                stored_count += 1
                
            except Exception as e:
                print(f"Error storing listing: {e}")
                continue
        
        return stored_count


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Vivanuncios scraper for Polpi MX')
    parser.add_argument('--test', action='store_true', help='Run in test mode (only 3 pages)')
    args = parser.parse_args()
    
    print("🏠 Starting Vivanuncios CDMX scraper")
    print("=" * 70)
    
    scraper = VivanunciosScraper()
    
    # Get current count
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "vivanuncios"')
    initial_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings')
    total_initial = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 Starting state:")
    print(f"   Vivanuncios listings: {initial_count}")
    print(f"   Total listings in DB: {total_initial}\n")
    
    # Scrape listings
    listings, stats = scraper.scrape_all_urls(test_mode=args.test)
    
    print(f"\n" + "=" * 70)
    print(f"📊 SCRAPING COMPLETE")
    print(f"   Total scraped: {len(listings)} listings")
    print(f"\n   Breakdown by type:")
    print(f"   SALES:")
    print(f"      Residential (casas/deptos): {stats['sale']['residential']}")
    print(f"      Land (terrenos): {stats['sale'].get('terreno', 0)}")
    print(f"      Commercial (locales/oficinas): {stats['sale']['comercial']}")
    print(f"      Subtotal: {sum(stats['sale'].values())}")
    print(f"\n   RENTALS:")
    print(f"      Residential (casas/deptos): {stats['rental']['residential']}")
    print(f"      Commercial (locales/oficinas): {stats['rental']['comercial']}")
    print(f"      Subtotal: {sum(stats['rental'].values())}")
    
    if listings:
        # Store in database
        print(f"\n💾 Storing in database...")
        stored = scraper.store_in_database(listings)
        print(f"   Stored {stored} listings")
        
        # Show sample listings by type
        sales_samples = [l for l in listings if l.get('listing_type') == 'sale'][:5]
        rental_samples = [l for l in listings if l.get('listing_type') == 'rental'][:3]
        
        if sales_samples:
            print(f"\n🏠 Sample SALES listings:")
            for i, listing in enumerate(sales_samples):
                price_str = f"${listing.get('price_mxn'):,.0f} MXN" if listing.get('price_mxn') else "N/A"
                prop_type = listing.get('property_type', 'N/A')
                size = listing.get('size_m2', 'N/A')
                beds = listing.get('bedrooms', 'N/A')
                print(f"   {i+1}. [{prop_type}] {listing.get('title', 'No title')[:50]}")
                print(f"      {price_str} | {size} m² | {beds} bed | {listing.get('colonia', 'N/A')}")
        
        if rental_samples:
            print(f"\n🔑 Sample RENTAL listings:")
            for i, listing in enumerate(rental_samples):
                price_str = f"${listing.get('price_mxn'):,.0f} MXN/mo" if listing.get('price_mxn') else "N/A"
                prop_type = listing.get('property_type', 'N/A')
                size = listing.get('size_m2', 'N/A')
                beds = listing.get('bedrooms', 'N/A')
                print(f"   {i+1}. [{prop_type}] {listing.get('title', 'No title')[:50]}")
                print(f"      {price_str} | {size} m² | {beds} bed | {listing.get('colonia', 'N/A')}")
    
    # Final counts
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "vivanuncios"')
    final_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "vivanuncios" AND listing_type = "sale"')
    final_sales = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings WHERE source = "vivanuncios" AND listing_type = "rental"')
    final_rentals = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM listings')
    total_final = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n" + "=" * 70)
    print(f"🎯 FINAL DATABASE STATUS")
    print(f"   Vivanuncios listings: {final_count} (added {final_count - initial_count})")
    print(f"      Sales: {final_sales}")
    print(f"      Rentals: {final_rentals}")
    print(f"   Total listings in DB: {total_final} (was {total_initial})")
    
    if args.test:
        print(f"\n🧪 Test mode complete - run without --test flag for full scrape")
    elif final_count - initial_count >= 200:
        print(f"\n🎉 SUCCESS! Added 200+ new listings from Vivanuncios!")
    elif final_count - initial_count > 0:
        print(f"\n✅ Added {final_count - initial_count} listings")
    else:
        print(f"\n⚠️ No new listings were added - may be blocked or duplicate data")
    
    print("=" * 70)
    
    return final_count


if __name__ == '__main__':
    main()
