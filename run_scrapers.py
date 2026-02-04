#!/usr/bin/env python3
"""Main scraper orchestrator - runs all scrapers and populates database"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from inmuebles24_scraper import Inmuebles24Scraper
from vivanuncios_scraper import VivanunciosScraper
from century21_scraper import Century21Scraper
from database import PolpiDB
import json
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

class DataPipeline:
    def __init__(self):
        self.db = PolpiDB()
        self.geocoder = Nominatim(user_agent="polpi-mx-prototype")
        self.geocode_cache = {}
    
    def geocode_location(self, city: str, colonia: str = None, state: str = None) -> tuple:
        """Geocode a location to lat/lng"""
        # Build query
        query_parts = []
        if colonia:
            query_parts.append(colonia)
        if city:
            query_parts.append(city)
        if state:
            query_parts.append(state)
        query_parts.append("Mexico")
        
        query = ", ".join(query_parts)
        
        # Check cache
        if query in self.geocode_cache:
            return self.geocode_cache[query]
        
        try:
            time.sleep(1)  # Rate limit
            location = self.geocoder.geocode(query, timeout=10)
            if location:
                result = (location.latitude, location.longitude)
                self.geocode_cache[query] = result
                return result
        except GeocoderTimedOut:
            print(f"Geocoding timeout for: {query}")
        except Exception as e:
            print(f"Geocoding error for {query}: {e}")
        
        return (None, None)
    
    def process_listing(self, raw_listing: dict) -> dict:
        """Process and normalize a raw listing"""
        listing = raw_listing.copy()
        
        # Geocode if no coordinates
        if not listing.get('lat') or not listing.get('lng'):
            if listing.get('city'):
                lat, lng = self.geocode_location(
                    listing.get('city'),
                    listing.get('colonia'),
                    listing.get('state')
                )
                if lat and lng:
                    listing['lat'] = lat
                    listing['lng'] = lng
        
        # Ensure price_usd if we have price_mxn
        if listing.get('price_mxn') and not listing.get('price_usd'):
            listing['price_usd'] = round(listing['price_mxn'] / 17.0, 2)
        
        # Store raw data for debugging
        listing['raw_data'] = json.dumps(raw_listing)
        
        return listing
    
    def detect_duplicates(self):
        """Detect and mark duplicate listings"""
        print("\nDetecting duplicates...")
        
        listings = self.db.get_listings(limit=10000)
        duplicates_found = 0
        
        for i, listing in enumerate(listings):
            for j in range(i + 1, len(listings)):
                other = listings[j]
                
                # Skip if same source
                if listing['source'] == other['source']:
                    continue
                
                # Check for duplicates based on:
                # - Same city and colonia
                # - Similar price (within 5%)
                # - Similar size (within 10%)
                
                if (listing.get('city') == other.get('city') and
                    listing.get('colonia') == other.get('colonia')):
                    
                    price_match = False
                    if listing.get('price_mxn') and other.get('price_mxn'):
                        price_diff = abs(listing['price_mxn'] - other['price_mxn']) / listing['price_mxn']
                        price_match = price_diff < 0.05
                    
                    size_match = False
                    if listing.get('size_m2') and other.get('size_m2'):
                        size_diff = abs(listing['size_m2'] - other['size_m2']) / listing['size_m2']
                        size_match = size_diff < 0.10
                    
                    if price_match and size_match:
                        print(f"Found duplicate: {listing['id']} <-> {other['id']}")
                        duplicates_found += 1
        
        print(f"Found {duplicates_found} potential duplicates")
    
    def run_all_scrapers(self, quick_mode: bool = False):
        """Run all scrapers and populate database"""
        print("=" * 60)
        print("POLPI MX - Data Scraping Pipeline")
        print("=" * 60)
        
        max_pages = 1 if quick_mode else 2
        all_listings = []
        
        # Scraper 1: Inmuebles24
        print("\n[1/3] Running Inmuebles24 scraper...")
        try:
            scraper1 = Inmuebles24Scraper()
            listings1 = scraper1.scrape(city='ciudad-de-mexico', max_pages=max_pages)
            all_listings.extend(listings1)
            print(f"✓ Inmuebles24: {len(listings1)} listings")
        except Exception as e:
            print(f"✗ Inmuebles24 failed: {e}")
        
        # Scraper 2: Vivanuncios
        print("\n[2/3] Running Vivanuncios scraper...")
        try:
            scraper2 = VivanunciosScraper()
            listings2 = scraper2.scrape(city='distrito-federal', max_pages=max_pages)
            all_listings.extend(listings2)
            print(f"✓ Vivanuncios: {len(listings2)} listings")
        except Exception as e:
            print(f"✗ Vivanuncios failed: {e}")
        
        # Scraper 3: Century21
        print("\n[3/3] Running Century21 scraper...")
        try:
            scraper3 = Century21Scraper()
            listings3 = scraper3.scrape(state='ciudad-de-mexico', max_pages=max_pages)
            all_listings.extend(listings3)
            print(f"✓ Century21: {len(listings3)} listings")
        except Exception as e:
            print(f"✗ Century21 failed: {e}")
        
        # Process and save listings
        print(f"\n{'='*60}")
        print(f"Processing {len(all_listings)} total listings...")
        
        success_count = 0
        for i, raw_listing in enumerate(all_listings):
            try:
                # Process listing (normalize, geocode, etc.)
                processed = self.process_listing(raw_listing)
                
                # Insert into database
                listing_id = self.db.insert_listing(processed)
                success_count += 1
                
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(all_listings)} listings...")
            
            except Exception as e:
                print(f"Error processing listing: {e}")
        
        print(f"\n✓ Successfully saved {success_count} listings to database")
        
        # Run duplicate detection
        self.detect_duplicates()
        
        # Print statistics
        stats = self.db.get_stats()
        print(f"\n{'='*60}")
        print("DATABASE STATISTICS")
        print(f"{'='*60}")
        print(f"Total listings: {stats['total_listings']}")
        print(f"Cities: {stats['cities']}")
        print(f"Colonias: {stats['colonias']}")
        print(f"\nListings by source:")
        for source, count in stats['sources'].items():
            print(f"  - {source}: {count}")
        
        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_scraped': len(all_listings),
            'total_saved': success_count,
            'stats': stats
        }
        
        os.makedirs('data', exist_ok=True)
        with open('data/scrape_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nSummary saved to data/scrape_summary.json")
        print(f"Database: data/polpi.db")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Polpi MX scrapers')
    parser.add_argument('--quick', action='store_true', help='Quick mode (1 page per scraper)')
    args = parser.parse_args()
    
    pipeline = DataPipeline()
    pipeline.run_all_scrapers(quick_mode=args.quick)
