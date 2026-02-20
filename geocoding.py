#!/usr/bin/env python3
"""
Geocoding helper for Polpi MX
Uses Nominatim (OpenStreetMap) for free geocoding of CDMX addresses
"""

import requests
import time
from typing import Optional, Tuple, Dict
from dataclasses import dataclass


@dataclass
class GeocodingResult:
    """Geocoding result container"""
    lat: float
    lng: float
    address: str
    colonia: Optional[str] = None
    city: Optional[str] = None
    delegacion: Optional[str] = None
    display_name: str = ""


class CDMXGeocoder:
    """Geocoder specifically tuned for CDMX addresses"""
    
    NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Polpi-MX/1.0 (Real Estate Analysis Tool)'
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Nominatim requires 1 req/sec max
    
    def _rate_limit(self):
        """Ensure we don't exceed Nominatim rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def geocode_address(self, address: str, city: str = "Ciudad de México") -> Optional[GeocodingResult]:
        """
        Geocode a CDMX address to lat/lng coordinates.
        
        Args:
            address: Street address or colonia name
            city: City name (defaults to Ciudad de México)
            
        Returns:
            GeocodingResult or None if not found
        """
        self._rate_limit()
        
        # Build search query
        query = f"{address}, {city}, México"
        
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'bounded': 1,
            'viewbox': '-99.36,19.59,-98.94,19.05',  # CDMX bounding box
        }
        
        try:
            response = self.session.get(
                f"{self.NOMINATIM_BASE}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                return None
            
            result = results[0]
            address_parts = result.get('address', {})
            
            return GeocodingResult(
                lat=float(result['lat']),
                lng=float(result['lon']),
                address=address,
                colonia=address_parts.get('suburb') or address_parts.get('neighbourhood'),
                city=address_parts.get('city') or address_parts.get('town') or city,
                delegacion=address_parts.get('city_district') or address_parts.get('state_district'),
                display_name=result.get('display_name', '')
            )
            
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            GeocodingResult or None if not found
        """
        self._rate_limit()
        
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'addressdetails': 1,
        }
        
        try:
            response = self.session.get(
                f"{self.NOMINATIM_BASE}/reverse",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            address_parts = result.get('address', {})
            
            # Extract street address
            street_parts = []
            if address_parts.get('road'):
                street_parts.append(address_parts['road'])
            if address_parts.get('house_number'):
                street_parts.append(address_parts['house_number'])
            
            address_str = ' '.join(street_parts) if street_parts else result.get('display_name', '')
            
            return GeocodingResult(
                lat=lat,
                lng=lng,
                address=address_str,
                colonia=address_parts.get('suburb') or address_parts.get('neighbourhood'),
                city=address_parts.get('city') or address_parts.get('town') or 'Ciudad de México',
                delegacion=address_parts.get('city_district') or address_parts.get('state_district'),
                display_name=result.get('display_name', '')
            )
            
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return None
    
    def search_colonia(self, colonia_name: str) -> Optional[GeocodingResult]:
        """
        Search for a colonia (neighborhood) by name.
        
        Args:
            colonia_name: Name of the colonia
            
        Returns:
            GeocodingResult or None if not found
        """
        # Append common CDMX colonia identifiers
        search_queries = [
            f"Colonia {colonia_name}, Ciudad de México, México",
            f"{colonia_name}, Ciudad de México, México",
        ]
        
        for query in search_queries:
            result = self.geocode_address(query)
            if result:
                return result
        
        return None


def parse_input(input_str: str) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
    """
    Parse user input to determine if it's an address or coordinates.
    
    Returns:
        (address, coordinates) tuple - one will be None
    """
    input_str = input_str.strip()
    
    # Check if it looks like coordinates (lat, lng)
    if ',' in input_str:
        parts = input_str.split(',')
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                
                # Basic validation for CDMX coordinates
                if 19.0 <= lat <= 19.6 and -99.4 <= lng <= -98.9:
                    return None, (lat, lng)
            except ValueError:
                pass
    
    # Otherwise treat as address
    return input_str, None


# Quick test
if __name__ == "__main__":
    geocoder = CDMXGeocoder()
    
    print("Testing geocoder...")
    print("=" * 60)
    
    # Test 1: Address geocoding
    print("\n1. Geocoding address: 'Polanco, Ciudad de México'")
    result = geocoder.geocode_address("Polanco")
    if result:
        print(f"   ✓ Found: {result.lat}, {result.lng}")
        print(f"   Colonia: {result.colonia}")
        print(f"   Delegación: {result.delegacion}")
    
    # Test 2: Reverse geocoding
    print("\n2. Reverse geocoding: 19.433, -99.133 (Centro Histórico)")
    result = geocoder.reverse_geocode(19.433, -99.133)
    if result:
        print(f"   ✓ Found: {result.colonia or result.address}")
        print(f"   Display: {result.display_name}")
    
    # Test 3: Colonia search
    print("\n3. Searching colonia: 'Roma Norte'")
    result = geocoder.search_colonia("Roma Norte")
    if result:
        print(f"   ✓ Found: {result.lat}, {result.lng}")
        print(f"   Colonia: {result.colonia}")
