#!/usr/bin/env python3
"""
Example integration of zoning lookup with Polpi MX database.
Demonstrates how to enrich existing listings with zoning data.
"""

import sqlite3
import json
from datetime import datetime
from zoning_lookup import SEDUVIZoningLookup, ZoningInfo
from database import PolpiDB


def add_zoning_columns():
    """
    Add zoning columns to the listings table.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("Adding zoning columns to database...")
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(listings)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    columns_to_add = {
        'zoning_category': 'TEXT',
        'zoning_category_full': 'TEXT',
        'zoning_max_floors': 'INTEGER',
        'zoning_max_cos': 'REAL',
        'zoning_max_cus': 'REAL',
        'zoning_allowed_uses': 'TEXT',
        'zoning_min_open_area_pct': 'REAL',
        'is_heritage_zone': 'BOOLEAN DEFAULT 0',
        'zoning_updated_date': 'TEXT',
    }
    
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE listings ADD COLUMN {col_name} {col_type}')
                print(f"  ✅ Added column: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️  Column {col_name} may already exist: {e}")
        else:
            print(f"  ℹ️  Column {col_name} already exists")
    
    conn.commit()
    conn.close()
    print("✅ Database schema updated!\n")


def enrich_single_listing(listing_id: str, use_mock_data: bool = True):
    """
    Enrich a single listing with zoning data.
    
    Args:
        listing_id: ID of listing to enrich
        use_mock_data: If True, use mock data. If False, attempt real SEDUVI lookup.
    """
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get listing
    cursor.execute('SELECT * FROM listings WHERE id = ?', (listing_id,))
    listing = cursor.fetchone()
    
    if not listing:
        print(f"❌ Listing {listing_id} not found")
        return
    
    # Check if listing has coordinates
    lat = listing['lat']
    lng = listing['lng']
    
    if not lat or not lng:
        print(f"⚠️  Listing {listing_id} has no coordinates, skipping")
        return
    
    print(f"🔍 Looking up zoning for listing {listing_id}")
    print(f"   Location: {lat}, {lng}")
    print(f"   Property: {listing['title']}")
    
    # Lookup zoning
    lookup = SEDUVIZoningLookup(use_mock_data=use_mock_data)
    zoning = lookup.lookup_by_coordinates(lat, lng)
    
    if not zoning:
        print(f"❌ No zoning data found")
        return
    
    # Update database
    cursor.execute('''
        UPDATE listings SET
            zoning_category = ?,
            zoning_category_full = ?,
            zoning_max_floors = ?,
            zoning_max_cos = ?,
            zoning_max_cus = ?,
            zoning_allowed_uses = ?,
            zoning_min_open_area_pct = ?,
            is_heritage_zone = ?,
            zoning_updated_date = ?
        WHERE id = ?
    ''', (
        zoning.category,
        zoning.category_full,
        zoning.max_floors,
        zoning.max_cos,
        zoning.max_cus,
        json.dumps(zoning.allowed_uses),
        zoning.min_open_area_pct,
        zoning.is_heritage_zone,
        datetime.now().isoformat(),
        listing_id
    ))
    
    conn.commit()
    
    print(f"✅ Updated listing with zoning data:")
    print(f"   Category: {zoning.category} - {zoning.category_full}")
    print(f"   Max Floors: {zoning.max_floors}")
    print(f"   Heritage Zone: {'Yes ⚠️' if zoning.is_heritage_zone else 'No'}")
    
    # Calculate buildable area if lot size is available
    if listing['lot_size_m2']:
        buildable = lookup.calculate_buildable_area(listing['lot_size_m2'], zoning)
        print(f"\n📐 Buildable Area Analysis:")
        print(f"   Lot Size: {listing['lot_size_m2']}m²")
        print(f"   Max Construction: {buildable.get('max_total_construction_m2', 'N/A')}m²")
        print(f"   Max Floors: {buildable.get('max_floors', 'N/A')}")
    
    conn.close()


def enrich_all_listings(limit: int = 100, use_mock_data: bool = True):
    """
    Enrich all listings that have coordinates but no zoning data.
    
    Args:
        limit: Maximum number of listings to process
        use_mock_data: If True, use mock data. If False, attempt real SEDUVI lookup.
    """
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get listings without zoning data
    cursor.execute('''
        SELECT id, title, lat, lng, lot_size_m2
        FROM listings
        WHERE lat IS NOT NULL 
          AND lng IS NOT NULL
          AND zoning_category IS NULL
        LIMIT ?
    ''', (limit,))
    
    listings = cursor.fetchall()
    conn.close()
    
    if not listings:
        print("✅ All listings with coordinates already have zoning data!")
        return
    
    print(f"🔄 Processing {len(listings)} listings...\n")
    
    lookup = SEDUVIZoningLookup(use_mock_data=use_mock_data)
    
    success_count = 0
    error_count = 0
    
    for listing in listings:
        listing_id = listing['id']
        lat = listing['lat']
        lng = listing['lng']
        
        try:
            # Lookup zoning
            zoning = lookup.lookup_by_coordinates(lat, lng)
            
            if zoning:
                # Update database
                conn = db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE listings SET
                        zoning_category = ?,
                        zoning_category_full = ?,
                        zoning_max_floors = ?,
                        zoning_max_cos = ?,
                        zoning_max_cus = ?,
                        zoning_allowed_uses = ?,
                        zoning_min_open_area_pct = ?,
                        is_heritage_zone = ?,
                        zoning_updated_date = ?
                    WHERE id = ?
                ''', (
                    zoning.category,
                    zoning.category_full,
                    zoning.max_floors,
                    zoning.max_cos,
                    zoning.max_cus,
                    json.dumps(zoning.allowed_uses),
                    zoning.min_open_area_pct,
                    zoning.is_heritage_zone,
                    datetime.now().isoformat(),
                    listing_id
                ))
                
                conn.commit()
                conn.close()
                
                heritage_flag = "⚠️ " if zoning.is_heritage_zone else ""
                print(f"✅ {heritage_flag}{listing_id}: {zoning.category} - {listing['title'][:50]}...")
                success_count += 1
            else:
                print(f"⚠️  {listing_id}: No zoning data found")
                error_count += 1
                
        except Exception as e:
            print(f"❌ {listing_id}: Error - {e}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully enriched: {success_count} listings")
    print(f"❌ Errors: {error_count}")
    print(f"{'='*60}")


def show_zoning_stats():
    """Display statistics about zoning data in the database."""
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Total listings
    cursor.execute('SELECT COUNT(*) FROM listings')
    total = cursor.fetchone()[0]
    
    # Listings with coordinates
    cursor.execute('SELECT COUNT(*) FROM listings WHERE lat IS NOT NULL AND lng IS NOT NULL')
    with_coords = cursor.fetchone()[0]
    
    # Listings with zoning data
    cursor.execute('SELECT COUNT(*) FROM listings WHERE zoning_category IS NOT NULL')
    with_zoning = cursor.fetchone()[0]
    
    # Heritage zones
    cursor.execute('SELECT COUNT(*) FROM listings WHERE is_heritage_zone = 1')
    heritage = cursor.fetchone()[0]
    
    # Zoning category breakdown
    cursor.execute('''
        SELECT zoning_category, COUNT(*) as count
        FROM listings
        WHERE zoning_category IS NOT NULL
        GROUP BY zoning_category
        ORDER BY count DESC
        LIMIT 10
    ''')
    category_stats = cursor.fetchall()
    
    conn.close()
    
    print("📊 Zoning Data Statistics")
    print("=" * 60)
    print(f"Total Listings: {total:,}")
    print(f"With Coordinates: {with_coords:,} ({with_coords/total*100:.1f}%)")
    print(f"With Zoning Data: {with_zoning:,} ({with_zoning/total*100 if total > 0 else 0:.1f}%)")
    print(f"Heritage Zones: {heritage:,}")
    
    if category_stats:
        print("\n🏙️ Top Zoning Categories:")
        for cat, count in category_stats:
            print(f"  {cat}: {count:,}")
    
    print("=" * 60)


def demo():
    """Run a demonstration of the zoning integration."""
    print("🏙️ Polpi MX - Zoning Integration Demo")
    print("=" * 60)
    print()
    
    # Step 1: Add columns (safe to run multiple times)
    print("Step 1: Database Schema")
    print("-" * 60)
    add_zoning_columns()
    
    # Step 2: Show current stats
    print("\nStep 2: Current Database Stats")
    print("-" * 60)
    show_zoning_stats()
    
    # Step 3: Enrich some listings
    print("\nStep 3: Enrich Listings with Zoning Data")
    print("-" * 60)
    print("Enriching first 10 listings with coordinates...")
    print("(Using mock data for demonstration)\n")
    
    enrich_all_listings(limit=10, use_mock_data=True)
    
    # Step 4: Show updated stats
    print("\nStep 4: Updated Statistics")
    print("-" * 60)
    show_zoning_stats()
    
    print("\n✅ Demo complete!")
    print("\nNext steps:")
    print("  1. Review updated listings in database")
    print("  2. Implement SEDUVI portal scraper (set use_mock_data=False)")
    print("  3. Run full enrichment: enrich_all_listings(limit=1000, use_mock_data=False)")
    print("  4. Add zoning display to frontend")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "add-columns":
            add_zoning_columns()
        elif command == "stats":
            show_zoning_stats()
        elif command == "enrich":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            use_mock = sys.argv[3].lower() != 'real' if len(sys.argv) > 3 else True
            enrich_all_listings(limit=limit, use_mock_data=use_mock)
        elif command == "enrich-one":
            if len(sys.argv) < 3:
                print("Usage: python integrate_zoning_example.py enrich-one <listing_id>")
            else:
                listing_id = sys.argv[2]
                enrich_single_listing(listing_id)
        else:
            print(f"Unknown command: {command}")
            print("Available commands: add-columns, stats, enrich, enrich-one")
    else:
        # Run full demo
        demo()
