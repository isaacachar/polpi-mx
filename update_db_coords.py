#!/usr/bin/env python3
"""
Update the SQLite database with geocoded coordinates from the JSON file
"""
import json
import sqlite3
from pathlib import Path

def main():
    # Load the geocoded JSON data
    json_path = Path("/Users/isaachomefolder/Desktop/polpi-mx/docs/js/data-listings.json")
    print(f"📖 Loading geocoded data from {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        listings = json.load(f)
    
    print(f"Found {len(listings)} listings in JSON")
    
    # Connect to database
    db_path = Path("/Users/isaachomefolder/Desktop/polpi-mx/data/polpi.db")
    print(f"\n🗄️  Connecting to {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check which table has the listings
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Found tables: {[t[0] for t in tables]}")
    
    # Assume the listings are in a table called 'listings' or 'properties'
    # Let's find it
    table_name = None
    for table in tables:
        t = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"  {t}: {count} rows")
        if count == 83 or 'listing' in t.lower() or 'propert' in t.lower():
            table_name = t
            print(f"  → Using table: {table_name}")
            break
    
    if not table_name:
        print("❌ Could not identify listings table")
        conn.close()
        return
    
    # Check table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\nTable schema:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")
    
    # Update coordinates for each listing
    print(f"\n📍 Updating coordinates in database...")
    updated = 0
    
    for listing in listings:
        listing_id = listing.get("id")
        lat = listing.get("lat")
        lng = listing.get("lng")
        
        if listing_id and lat is not None and lng is not None:
            try:
                cursor.execute(
                    f"UPDATE {table_name} SET lat = ?, lng = ? WHERE id = ?",
                    (lat, lng, listing_id)
                )
                if cursor.rowcount > 0:
                    updated += 1
            except Exception as e:
                print(f"  Error updating {listing_id}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated}/{len(listings)} listings in database")

if __name__ == "__main__":
    main()
