#!/usr/bin/env python3
"""Enhanced database schema and operations for Polpi MX"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
from config import config

class PolpiDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Create enhanced database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Main listings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_id TEXT,
                url TEXT,
                title TEXT,
                price_mxn REAL,
                price_usd REAL,
                property_type TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size_m2 REAL,
                lot_size_m2 REAL,
                state TEXT,
                city TEXT,
                colonia TEXT,
                lat REAL,
                lng REAL,
                description TEXT,
                images TEXT,
                agent_name TEXT,
                agent_phone TEXT,
                listed_date TEXT,
                scraped_date TEXT NOT NULL,
                amenities TEXT,
                parking_spaces INTEGER,
                data_quality_score REAL,
                raw_data TEXT,
                is_active BOOLEAN DEFAULT 1,
                views_count INTEGER DEFAULT 0,
                UNIQUE(source, source_id)
            )
        ''')
        
        # Full-text search virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS listings_fts USING fts5(
                id UNINDEXED,
                title,
                description,
                city,
                colonia,
                amenities
            )
        ''')
        
        # Duplicate tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duplicates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_id TEXT NOT NULL,
                duplicate_id TEXT NOT NULL,
                confidence REAL,
                FOREIGN KEY (canonical_id) REFERENCES listings(id),
                FOREIGN KEY (duplicate_id) REFERENCES listings(id)
            )
        ''')
        
        # Enhanced price history for trend tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id TEXT NOT NULL,
                price_mxn REAL,
                price_usd REAL,
                recorded_date TEXT NOT NULL,
                source TEXT,
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            )
        ''')
        
        # Market trends table for city-level monthly averages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                colonia TEXT,
                property_type TEXT,
                year_month TEXT NOT NULL,  -- Format: YYYY-MM
                avg_price_mxn REAL,
                avg_price_per_m2 REAL,
                median_price_mxn REAL,
                listing_count INTEGER,
                created_date TEXT NOT NULL,
                UNIQUE(city, colonia, property_type, year_month)
            )
        ''')
        
        # Neighborhood statistics cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS neighborhood_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                colonia TEXT,
                property_type TEXT,
                avg_price_mxn REAL,
                avg_price_per_m2 REAL,
                median_price_mxn REAL,
                p25_price_mxn REAL,
                p75_price_mxn REAL,
                p90_price_mxn REAL,
                listing_count INTEGER,
                last_updated TEXT,
                UNIQUE(city, colonia, property_type)
            )
        ''')
        
        # Create comprehensive indexes for performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_city ON listings(city)',
            'CREATE INDEX IF NOT EXISTS idx_colonia ON listings(colonia)',
            'CREATE INDEX IF NOT EXISTS idx_property_type ON listings(property_type)',
            'CREATE INDEX IF NOT EXISTS idx_price ON listings(price_mxn)',
            'CREATE INDEX IF NOT EXISTS idx_price_per_m2 ON listings(price_mxn, size_m2)',
            'CREATE INDEX IF NOT EXISTS idx_location ON listings(lat, lng)',
            'CREATE INDEX IF NOT EXISTS idx_size ON listings(size_m2)',
            'CREATE INDEX IF NOT EXISTS idx_bedrooms ON listings(bedrooms)',
            'CREATE INDEX IF NOT EXISTS idx_bathrooms ON listings(bathrooms)',
            'CREATE INDEX IF NOT EXISTS idx_scraped_date ON listings(scraped_date)',
            'CREATE INDEX IF NOT EXISTS idx_listed_date ON listings(listed_date)',
            'CREATE INDEX IF NOT EXISTS idx_active ON listings(is_active)',
            'CREATE INDEX IF NOT EXISTS idx_data_quality ON listings(data_quality_score)',
            'CREATE INDEX IF NOT EXISTS idx_city_colonia_type ON listings(city, colonia, property_type)',
            
            # Price history indexes
            'CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id)',
            'CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_date)',
            
            # Market trends indexes
            'CREATE INDEX IF NOT EXISTS idx_market_trends_city ON market_trends(city)',
            'CREATE INDEX IF NOT EXISTS idx_market_trends_date ON market_trends(year_month)',
            'CREATE INDEX IF NOT EXISTS idx_market_trends_combo ON market_trends(city, property_type, year_month)',
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        
        # Initialize sample historical data if empty
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Create sample historical data for market trends"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if we have any market trends data
        cursor.execute("SELECT COUNT(*) as count FROM market_trends")
        count = cursor.fetchone()['count']
        
        if count == 0:
            print("Generating sample historical market data...")
            self._generate_historical_trends()
        
        conn.close()
    
    def _generate_historical_trends(self):
        """Generate 12 months of historical trend data for each city"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get unique cities and property types
        cursor.execute("""
            SELECT DISTINCT city, property_type, COUNT(*) as count
            FROM listings 
            WHERE city IS NOT NULL AND property_type IS NOT NULL
            GROUP BY city, property_type
            HAVING count >= 3
        """)
        
        city_types = cursor.fetchall()
        
        # Generate 12 months of data going back
        current_date = datetime.now()
        for i in range(12):
            month_date = current_date - timedelta(days=i*30)
            year_month = month_date.strftime('%Y-%m')
            
            for row in city_types:
                city = row['city']
                property_type = row['property_type']
                
                # Get current average for this city/type
                cursor.execute("""
                    SELECT 
                        AVG(price_mxn) as avg_price,
                        AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2,
                        COUNT(*) as count
                    FROM listings
                    WHERE city = ? AND property_type = ?
                """, (city, property_type))
                
                current = cursor.fetchone()
                if current['avg_price']:
                    # Add some variation (-15% to +15%) and trend
                    trend_factor = 1 + (i * 0.002)  # Slight upward trend over time
                    variation = 1 + random.uniform(-0.15, 0.15)
                    
                    avg_price = current['avg_price'] * trend_factor * variation
                    avg_price_per_m2 = current['avg_price_per_m2'] * trend_factor * variation if current['avg_price_per_m2'] else None
                    
                    # Insert trend data
                    cursor.execute("""
                        INSERT OR IGNORE INTO market_trends 
                        (city, property_type, year_month, avg_price_mxn, avg_price_per_m2, 
                         median_price_mxn, listing_count, created_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        city, property_type, year_month, 
                        round(avg_price, 2),
                        round(avg_price_per_m2, 2) if avg_price_per_m2 else None,
                        round(avg_price * 0.95, 2),  # Approximate median
                        max(1, int(current['count'] * random.uniform(0.8, 1.2))),
                        month_date.isoformat()
                    ))
        
        conn.commit()
        conn.close()
    
    def generate_listing_id(self, source: str, url: str, title: str) -> str:
        """Generate unique listing ID"""
        data = f"{source}:{url}:{title}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def insert_listing(self, listing: Dict) -> str:
        """Insert or update a listing with FTS support"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate ID if not provided
        if 'id' not in listing:
            listing['id'] = self.generate_listing_id(
                listing['source'],
                listing.get('url', ''),
                listing.get('title', '')
            )
        
        # Convert lists to JSON
        if 'images' in listing and isinstance(listing['images'], list):
            listing['images'] = json.dumps(listing['images'])
        if 'amenities' in listing and isinstance(listing['amenities'], list):
            listing['amenities'] = json.dumps(listing['amenities'])
        
        # Calculate data quality score
        listing['data_quality_score'] = self.calculate_quality_score(listing)
        
        # Add scraped date
        listing['scraped_date'] = datetime.now().isoformat()
        
        # Store raw data
        if 'raw_data' in listing and isinstance(listing['raw_data'], dict):
            listing['raw_data'] = json.dumps(listing['raw_data'])
        
        columns = ', '.join(listing.keys())
        placeholders = ', '.join(['?' for _ in listing])
        
        try:
            cursor.execute(f'''
                INSERT OR REPLACE INTO listings ({columns})
                VALUES ({placeholders})
            ''', list(listing.values()))
            
            # Update FTS index
            amenities_str = listing.get('amenities', '')
            if isinstance(amenities_str, str) and amenities_str.startswith('['):
                try:
                    amenities_str = ' '.join(json.loads(amenities_str))
                except:
                    pass
            
            cursor.execute('''
                INSERT OR REPLACE INTO listings_fts 
                (id, title, description, city, colonia, amenities)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                listing['id'],
                listing.get('title', ''),
                listing.get('description', ''),
                listing.get('city', ''),
                listing.get('colonia', ''),
                amenities_str
            ))
            
            # Record price history
            if 'price_mxn' in listing and listing['price_mxn']:
                cursor.execute('''
                    INSERT INTO price_history (listing_id, price_mxn, recorded_date)
                    VALUES (?, ?, ?)
                ''', (
                    listing['id'], 
                    listing['price_mxn'], 
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            return listing['id']
        except Exception as e:
            print(f"Error inserting listing: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def calculate_quality_score(self, listing: Dict) -> float:
        """Calculate data quality score (0-1)"""
        score = 0.0
        total_fields = 15
        
        # Required fields
        if listing.get('price_mxn'): score += 1
        if listing.get('property_type'): score += 1
        if listing.get('city'): score += 1
        if listing.get('colonia'): score += 1
        if listing.get('size_m2'): score += 1
        
        # Optional but valuable fields
        if listing.get('bedrooms') is not None: score += 1
        if listing.get('bathrooms') is not None: score += 1
        if listing.get('lat') and listing.get('lng'): score += 1
        if listing.get('description'): score += 1
        if listing.get('images'): score += 1
        if listing.get('agent_name'): score += 1
        if listing.get('agent_phone'): score += 1
        if listing.get('url'): score += 1
        if listing.get('amenities'): score += 1
        if listing.get('lot_size_m2'): score += 1
        
        return round(score / total_fields, 2)
    
    def get_listings_paginated(self, filters: Dict = None, page: int = 1, 
                             per_page: int = None, sort_by: str = 'newest') -> Dict:
        """Get listings with pagination and sorting"""
        per_page = per_page or config.DEFAULT_PAGE_SIZE
        per_page = min(per_page, config.MAX_PAGE_SIZE)
        offset = (page - 1) * per_page
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build query
        base_query = "FROM listings WHERE is_active = 1"
        count_query = f"SELECT COUNT(*) as total {base_query}"
        params = []
        
        if filters:
            filter_conditions = []
            if filters.get('city'):
                filter_conditions.append("city = ?")
                params.append(filters['city'])
            if filters.get('colonia'):
                filter_conditions.append("colonia = ?")
                params.append(filters['colonia'])
            if filters.get('property_type'):
                filter_conditions.append("property_type = ?")
                params.append(filters['property_type'])
            if filters.get('min_price'):
                filter_conditions.append("price_mxn >= ?")
                params.append(filters['min_price'])
            if filters.get('max_price'):
                filter_conditions.append("price_mxn <= ?")
                params.append(filters['max_price'])
            if filters.get('bedrooms'):
                filter_conditions.append("bedrooms >= ?")
                params.append(filters['bedrooms'])
            if filters.get('bathrooms'):
                filter_conditions.append("bathrooms >= ?")
                params.append(filters['bathrooms'])
            if filters.get('min_size'):
                filter_conditions.append("size_m2 >= ?")
                params.append(filters['min_size'])
            if filters.get('max_size'):
                filter_conditions.append("size_m2 <= ?")
                params.append(filters['max_size'])
            
            if filter_conditions:
                base_query += " AND " + " AND ".join(filter_conditions)
                count_query += " AND " + " AND ".join(filter_conditions)
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Add sorting
        sort_mapping = {
            'newest': 'scraped_date DESC',
            'price': 'price_mxn ASC',
            'price_desc': 'price_mxn DESC',
            'size': 'size_m2 DESC',
            'price_per_m2': '(price_mxn / NULLIF(size_m2, 0)) ASC',
            'deal_score': 'data_quality_score DESC'  # Placeholder for actual deal score
        }
        
        order_clause = sort_mapping.get(sort_by, sort_mapping['newest'])
        
        # Get listings
        listings_query = f"""
            SELECT *, 
                   CASE WHEN size_m2 > 0 THEN price_mxn / size_m2 ELSE NULL END as price_per_m2
            {base_query}
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(listings_query, params + [per_page, offset])
        rows = cursor.fetchall()
        conn.close()
        
        listings = []
        for row in rows:
            listing = dict(row)
            # Parse JSON fields
            if listing.get('images'):
                try:
                    listing['images'] = json.loads(listing['images'])
                except:
                    listing['images'] = []
            if listing.get('amenities'):
                try:
                    listing['amenities'] = json.loads(listing['amenities'])
                except:
                    listing['amenities'] = []
            listings.append(listing)
        
        return {
            'listings': listings,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'has_next': page * per_page < total,
            'has_prev': page > 1
        }
    
    def search_listings(self, query: str, page: int = 1, per_page: int = None) -> Dict:
        """Full-text search across listings"""
        if len(query.strip()) < config.SEARCH_MIN_LENGTH:
            return {
                'listings': [],
                'total': 0,
                'page': page,
                'per_page': per_page or config.DEFAULT_PAGE_SIZE,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False
            }
        
        per_page = per_page or config.DEFAULT_PAGE_SIZE
        per_page = min(per_page, config.MAX_PAGE_SIZE)
        offset = (page - 1) * per_page
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Search using FTS5
        search_query = f'"{query.strip()}"'
        
        # Get total count
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM listings_fts 
            WHERE listings_fts MATCH ?
        """, (search_query,))
        total = cursor.fetchone()['total']
        
        # Get results with full listing data
        cursor.execute("""
            SELECT l.*, 
                   CASE WHEN l.size_m2 > 0 THEN l.price_mxn / l.size_m2 ELSE NULL END as price_per_m2
            FROM listings_fts fts
            JOIN listings l ON l.id = fts.id
            WHERE listings_fts MATCH ?
            ORDER BY l.scraped_date DESC
            LIMIT ? OFFSET ?
        """, (search_query, per_page, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        listings = []
        for row in rows:
            listing = dict(row)
            # Parse JSON fields
            if listing.get('images'):
                try:
                    listing['images'] = json.loads(listing['images'])
                except:
                    listing['images'] = []
            if listing.get('amenities'):
                try:
                    listing['amenities'] = json.loads(listing['amenities'])
                except:
                    listing['amenities'] = []
            listings.append(listing)
        
        return {
            'listings': listings,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'has_next': page * per_page < total,
            'has_prev': page > 1
        }
    
    def get_neighborhood_stats_enhanced(self, city: str, colonia: str, property_type: str = None) -> Dict:
        """Get enhanced neighborhood statistics with percentiles"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                price_mxn,
                price_mxn / NULLIF(size_m2, 0) as price_per_m2
            FROM listings
            WHERE city = ? AND colonia = ? AND price_mxn > 0 AND size_m2 > 0
        """
        params = [city, colonia]
        
        if property_type:
            query += " AND property_type = ?"
            params.append(property_type)
        
        query += " ORDER BY price_mxn"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        prices = [row['price_mxn'] for row in rows]
        prices_per_m2 = [row['price_per_m2'] for row in rows if row['price_per_m2']]
        
        def percentile(data, p):
            """Calculate percentile"""
            if not data:
                return None
            n = len(data)
            index = (p / 100) * (n - 1)
            if index == int(index):
                return data[int(index)]
            else:
                lower = data[int(index)]
                upper = data[int(index) + 1]
                return lower + (upper - lower) * (index - int(index))
        
        return {
            'city': city,
            'colonia': colonia,
            'property_type': property_type,
            'listing_count': len(prices),
            'avg_price_mxn': round(sum(prices) / len(prices), 2),
            'median_price_mxn': round(percentile(prices, 50), 2),
            'p25_price_mxn': round(percentile(prices, 25), 2),
            'p75_price_mxn': round(percentile(prices, 75), 2),
            'p90_price_mxn': round(percentile(prices, 90), 2),
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price_per_m2': round(sum(prices_per_m2) / len(prices_per_m2), 2) if prices_per_m2 else None,
            'median_price_per_m2': round(percentile(sorted(prices_per_m2), 50), 2) if prices_per_m2 else None
        }
    
    def get_market_trends(self, city: str, property_type: str = None, months: int = 12) -> List[Dict]:
        """Get market trends for a city"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM market_trends
            WHERE city = ?
        """
        params = [city]
        
        if property_type:
            query += " AND property_type = ?"
            params.append(property_type)
        
        query += " ORDER BY year_month DESC LIMIT ?"
        params.append(months)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_cities_with_stats(self) -> List[Dict]:
        """Get list of cities with statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                city,
                COUNT(*) as listing_count,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2,
                MIN(price_mxn) as min_price,
                MAX(price_mxn) as max_price
            FROM listings
            WHERE city IS NOT NULL AND is_active = 1
            GROUP BY city
            ORDER BY listing_count DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_listings(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """Legacy method for backward compatibility"""
        result = self.get_listings_paginated(filters, page=1, per_page=limit, sort_by='newest')
        return result['listings']
    
    def get_neighborhood_stats(self, city: str, colonia: str, property_type: str = None) -> Dict:
        """Legacy method for backward compatibility"""
        return self.get_neighborhood_stats_enhanced(city, colonia, property_type)
    
    def find_comparables(self, listing_id: str, limit: int = 5) -> List[Dict]:
        """Find comparable properties (unchanged from original)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get the listing
        cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        listing = cursor.fetchone()
        
        if not listing:
            conn.close()
            return []
        
        # Find similar properties
        query = """
            SELECT *,
                ABS(size_m2 - ?) as size_diff,
                ABS(price_mxn - ?) as price_diff,
                CASE WHEN size_m2 > 0 THEN price_mxn / size_m2 ELSE NULL END as price_per_m2
            FROM listings
            WHERE id != ?
                AND city = ?
                AND property_type = ?
                AND size_m2 BETWEEN ? AND ?
                AND is_active = 1
        """
        
        size_tolerance = 0.3  # 30% size variance
        min_size = listing['size_m2'] * (1 - size_tolerance) if listing['size_m2'] else 0
        max_size = listing['size_m2'] * (1 + size_tolerance) if listing['size_m2'] else 999999
        
        params = [
            listing['size_m2'] or 0,
            listing['price_mxn'] or 0,
            listing_id,
            listing['city'],
            listing['property_type'],
            min_size,
            max_size
        ]
        
        # Prefer same colonia
        if listing['colonia']:
            query += " AND colonia = ?"
            params.append(listing['colonia'])
        
        query += " ORDER BY size_diff ASC, price_diff ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        comparables = []
        for row in rows:
            comp = dict(row)
            if comp.get('images'):
                try:
                    comp['images'] = json.loads(comp['images'])
                except:
                    comp['images'] = []
            comparables.append(comp)
        
        return comparables
    
    def get_stats(self) -> Dict:
        """Get overall database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM listings WHERE is_active = 1")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(DISTINCT city) as cities FROM listings WHERE is_active = 1")
        cities = cursor.fetchone()['cities']
        
        cursor.execute("SELECT COUNT(DISTINCT colonia) as colonias FROM listings WHERE is_active = 1")
        colonias = cursor.fetchone()['colonias']
        
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM listings 
            WHERE is_active = 1 
            GROUP BY source
        """)
        sources = {row['source']: row['count'] for row in cursor.fetchall()}
        
        # Get average prices by property type
        cursor.execute("""
            SELECT 
                property_type,
                COUNT(*) as count,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
            FROM listings
            WHERE is_active = 1 AND property_type IS NOT NULL
            GROUP BY property_type
            ORDER BY count DESC
        """)
        property_types = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total_listings': total,
            'cities': cities,
            'colonias': colonias,
            'sources': sources,
            'property_types': property_types
        }