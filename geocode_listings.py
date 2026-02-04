#!/usr/bin/env python3
"""
Geocode all listings in docs/js/data-listings.json using Nominatim API
"""
import json
import time
import random
import urllib.request
import urllib.parse
from pathlib import Path
from collections import defaultdict

def geocode_colonia(colonia):
    """Geocode a colonia using Nominatim API"""
    # Prepare search query - include "Mexico" to improve accuracy
    query = f"{colonia}, Mexico"
    
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1
    })
    
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PolpiMX/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            results = json.loads(data)
        
        if results:
            lat = float(results[0]["lat"])
            lng = float(results[0]["lon"])
            print(f"✓ Geocoded: {colonia} → ({lat:.6f}, {lng:.6f})")
            return lat, lng
        else:
            print(f"✗ No results for: {colonia}")
            return None, None
    except Exception as e:
        print(f"✗ Error geocoding {colonia}: {e}")
        return None, None

def add_jitter(lat, lng, jitter_amount=0.002):
    """Add random jitter to coordinates to prevent marker stacking"""
    jitter_lat = random.uniform(-jitter_amount, jitter_amount)
    jitter_lng = random.uniform(-jitter_amount, jitter_amount)
    return lat + jitter_lat, lng + jitter_lng

def main():
    # Read listings
    listings_path = Path("/Users/isaachomefolder/Desktop/polpi-mx/docs/js/data-listings.json")
    print(f"\n📖 Reading {listings_path}...")
    
    with open(listings_path, 'r', encoding='utf-8') as f:
        listings = json.load(f)
    
    print(f"Found {len(listings)} listings")
    
    # Group listings by colonia
    colonias_map = defaultdict(list)
    for idx, listing in enumerate(listings):
        colonia = listing.get("colonia")
        if colonia:
            colonias_map[colonia].append(idx)
    
    unique_colonias = list(colonias_map.keys())
    print(f"Found {len(unique_colonias)} unique colonias")
    print("\nColonias to geocode:")
    for colonia in sorted(unique_colonias):
        count = len(colonias_map[colonia])
        print(f"  - {colonia} ({count} listings)")
    
    # Geocode each unique colonia
    print("\n🌍 Starting geocoding (respecting 1 req/sec rate limit)...")
    colonia_coords = {}
    
    for i, colonia in enumerate(sorted(unique_colonias)):
        print(f"\n[{i+1}/{len(unique_colonias)}] ", end="")
        
        lat, lng = geocode_colonia(colonia)
        if lat and lng:
            colonia_coords[colonia] = (lat, lng)
        
        # Respect Nominatim rate limit: 1 request per second
        if i < len(unique_colonias) - 1:
            time.sleep(1.1)
    
    # Update listings with geocoded coordinates (with jitter)
    print("\n\n📍 Applying coordinates to listings...")
    updated_count = 0
    
    for listing in listings:
        colonia = listing.get("colonia")
        if colonia in colonia_coords:
            base_lat, base_lng = colonia_coords[colonia]
            jittered_lat, jittered_lng = add_jitter(base_lat, base_lng)
            
            listing["lat"] = round(jittered_lat, 6)
            listing["lng"] = round(jittered_lng, 6)
            updated_count += 1
    
    print(f"Updated {updated_count}/{len(listings)} listings with coordinates")
    
    # Save updated listings
    print(f"\n💾 Saving updated listings to {listings_path}...")
    with open(listings_path, 'w', encoding='utf-8') as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Geocoding complete!")
    
    # Summary
    print("\n📊 Summary:")
    print(f"  Total listings: {len(listings)}")
    print(f"  Updated with coordinates: {updated_count}")
    print(f"  Missing coordinates: {len(listings) - updated_count}")
    print(f"\n  Unique colonias geocoded: {len(colonia_coords)}/{len(unique_colonias)}")
    
    if len(colonia_coords) < len(unique_colonias):
        print("\n⚠️  Some colonias could not be geocoded:")
        for colonia in sorted(unique_colonias):
            if colonia not in colonia_coords:
                count = len(colonias_map[colonia])
                print(f"    - {colonia} ({count} listings)")

if __name__ == "__main__":
    main()
