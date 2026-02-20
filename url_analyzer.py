#!/usr/bin/env python3
"""
URL Analyzer for Polpi MX - Extract property data from individual listing URLs
Supports: Lamudi, MercadoLibre, Inmuebles24
"""

import re
import requests
import cloudscraper
from bs4 import BeautifulSoup
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class PropertyData:
    """Extracted property data from listing URL"""
    url: str
    source: str
    title: Optional[str] = None
    price_mxn: Optional[float] = None
    size_m2: Optional[float] = None
    lot_size_m2: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    city: Optional[str] = None
    colonia: Optional[str] = None
    state: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    description: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class URLAnalyzer:
    """Extract property data from listing URLs"""
    
    def __init__(self):
        # Standard requests session for most sites
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
        })
        
        # Cloudscraper for sites with Cloudflare
        self.cloudscraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'darwin', 'mobile': False}
        )
    
    def analyze_url(self, url: str) -> Optional[PropertyData]:
        """
        Analyze a property listing URL and extract data.
        
        Args:
            url: Property listing URL
            
        Returns:
            PropertyData object or None if extraction failed
        """
        url = url.strip()
        
        # Detect source from URL
        if 'lamudi.com.mx' in url:
            return self._extract_lamudi(url)
        elif 'mercadolibre.com.mx' in url or 'inmuebles.mercadolibre.com.mx' in url:
            return self._extract_mercadolibre(url)
        elif 'inmuebles24.com' in url:
            return self._extract_inmuebles24(url)
        else:
            raise ValueError(f"Unsupported URL source. Supported: Lamudi, MercadoLibre, Inmuebles24")
    
    def _extract_lamudi(self, url: str) -> Optional[PropertyData]:
        """Extract data from Lamudi listing"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = PropertyData(url=url, source='lamudi')
            
            # Title
            title_elem = soup.find('h1', class_='Title')
            if title_elem:
                data.title = title_elem.get_text(strip=True)
            
            # Price
            price_elem = soup.find('span', class_='PriceSection__Price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    data.price_mxn = float(price_match.group(0))
            
            # Property details
            details = soup.find_all('div', class_='KeyInformation__item')
            for detail in details:
                label_elem = detail.find('span', class_='KeyInformation__item-label')
                value_elem = detail.find('span', class_='KeyInformation__item-value')
                
                if not label_elem or not value_elem:
                    continue
                
                label = label_elem.get_text(strip=True).lower()
                value = value_elem.get_text(strip=True)
                
                if 'recámara' in label or 'bedroom' in label:
                    data.bedrooms = self._parse_int(value)
                elif 'baño' in label or 'bathroom' in label:
                    data.bathrooms = self._parse_int(value)
                elif 'm²' in label or 'área' in label or 'size' in label:
                    data.size_m2 = self._parse_float(value)
                elif 'terreno' in label or 'land' in label or 'lote' in label:
                    data.lot_size_m2 = self._parse_float(value)
                elif 'tipo' in label or 'type' in label:
                    data.property_type = value
            
            # Location
            location_elem = soup.find('div', class_='Location__address')
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                # Parse "Colonia, Alcaldía/Municipio, Ciudad de México"
                parts = [p.strip() for p in location_text.split(',')]
                if len(parts) >= 1:
                    data.colonia = parts[0]
                if len(parts) >= 2:
                    data.city = parts[-1] if 'méxico' in parts[-1].lower() else 'Ciudad de México'
                    data.state = 'Ciudad de México'
            
            # Description
            desc_elem = soup.find('div', class_='Description__content')
            if desc_elem:
                data.description = desc_elem.get_text(strip=True)[:500]  # First 500 chars
            
            # Try to extract coordinates from map script
            coords = self._extract_coordinates_from_script(soup)
            if coords:
                data.lat, data.lng = coords
            
            return data
            
        except Exception as e:
            print(f"Error extracting Lamudi data: {e}")
            return None
    
    def _extract_mercadolibre(self, url: str) -> Optional[PropertyData]:
        """Extract data from MercadoLibre listing"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = PropertyData(url=url, source='mercadolibre')
            
            # Title
            title_elem = soup.find('h1', class_='ui-pdp-title')
            if title_elem:
                data.title = title_elem.get_text(strip=True)
            
            # Price
            price_elem = soup.find('span', class_='andes-money-amount__fraction')
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace(',', '')
                data.price_mxn = self._parse_float(price_text)
            
            # Property details from specs table
            specs = soup.find_all('tr', class_='andes-table__row')
            for spec in specs:
                header = spec.find('th', class_='andes-table__header')
                cell = spec.find('td', class_='andes-table__column')
                
                if not header or not cell:
                    continue
                
                label = header.get_text(strip=True).lower()
                value = cell.get_text(strip=True)
                
                if 'superficie total' in label or 'área total' in label:
                    data.size_m2 = self._parse_float(value)
                elif 'superficie terreno' in label or 'terreno' in label:
                    data.lot_size_m2 = self._parse_float(value)
                elif 'recámara' in label or 'dormitorio' in label:
                    data.bedrooms = self._parse_int(value)
                elif 'baño' in label:
                    data.bathrooms = self._parse_int(value)
                elif 'tipo de propiedad' in label or 'tipo de inmueble' in label:
                    data.property_type = value
                elif 'ubicación' in label:
                    # Parse location
                    parts = [p.strip() for p in value.split(',')]
                    if parts:
                        data.colonia = parts[0]
                    if len(parts) > 1:
                        data.city = parts[1] if parts[1] else 'Ciudad de México'
                        data.state = 'Ciudad de México'
            
            # Description
            desc_elem = soup.find('p', class_='ui-pdp-description__content')
            if desc_elem:
                data.description = desc_elem.get_text(strip=True)[:500]
            
            # Try to extract coordinates
            coords = self._extract_coordinates_from_script(soup)
            if coords:
                data.lat, data.lng = coords
            
            return data
            
        except Exception as e:
            print(f"Error extracting MercadoLibre data: {e}")
            return None
    
    def _extract_inmuebles24(self, url: str) -> Optional[PropertyData]:
        """Extract data from Inmuebles24 listing"""
        try:
            # Inmuebles24 uses Cloudflare, need cloudscraper
            response = self.cloudscraper.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = PropertyData(url=url, source='inmuebles24')
            
            # Title
            title_elem = soup.find('h1', class_=lambda x: x and 'property-title' in x if x else False)
            if not title_elem:
                title_elem = soup.find('h1')
            if title_elem:
                data.title = title_elem.get_text(strip=True)
            
            # Price
            price_elem = soup.find('span', class_=lambda x: x and 'price-tag' in x if x else False)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+', price_text.replace(',', ''))
                if price_match:
                    data.price_mxn = float(price_match.group(0))
            
            # Features section
            features = soup.find_all('li', class_=lambda x: x and 'feature' in x if x else False)
            for feature in features:
                text = feature.get_text(strip=True).lower()
                
                if 'recámara' in text or 'dormitorio' in text:
                    data.bedrooms = self._parse_int(text)
                elif 'baño' in text:
                    data.bathrooms = self._parse_int(text)
                elif 'm²' in text or 'm2' in text:
                    if 'terreno' in text or 'lote' in text:
                        data.lot_size_m2 = self._parse_float(text)
                    else:
                        data.size_m2 = self._parse_float(text)
            
            # Location
            location_elem = soup.find('h2', class_=lambda x: x and 'location' in x if x else False)
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                parts = [p.strip() for p in location_text.split(',')]
                if parts:
                    data.colonia = parts[0]
                    data.city = 'Ciudad de México'
                    data.state = 'Ciudad de México'
            
            # Description
            desc_elem = soup.find('div', class_=lambda x: x and 'description' in x if x else False)
            if desc_elem:
                data.description = desc_elem.get_text(strip=True)[:500]
            
            # Property type from breadcrumbs or title
            if data.title:
                title_lower = data.title.lower()
                if 'departamento' in title_lower or 'apartment' in title_lower:
                    data.property_type = 'Departamento'
                elif 'casa' in title_lower or 'house' in title_lower:
                    data.property_type = 'Casa'
                elif 'terreno' in title_lower or 'land' in title_lower:
                    data.property_type = 'Terreno'
            
            # Try to extract coordinates
            coords = self._extract_coordinates_from_script(soup)
            if coords:
                data.lat, data.lng = coords
            
            return data
            
        except Exception as e:
            print(f"Error extracting Inmuebles24 data: {e}")
            return None
    
    def _extract_coordinates_from_script(self, soup: BeautifulSoup) -> Optional[tuple]:
        """Try to extract lat/lng from JavaScript in page"""
        scripts = soup.find_all('script')
        
        for script in scripts:
            script_text = script.string if script.string else ''
            
            # Look for common patterns
            # Pattern 1: lat: 19.xxx, lng: -99.xxx
            match = re.search(r'lat["\s:]+(-?\d+\.\d+).*?lng["\s:]+(-?\d+\.\d+)', script_text, re.IGNORECASE)
            if match:
                return float(match.group(1)), float(match.group(2))
            
            # Pattern 2: latitude, longitude
            match = re.search(r'latitude["\s:]+(-?\d+\.\d+).*?longitude["\s:]+(-?\d+\.\d+)', script_text, re.IGNORECASE)
            if match:
                return float(match.group(1)), float(match.group(2))
            
            # Pattern 3: Array [lat, lng]
            match = re.search(r'\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]', script_text)
            if match:
                lat, lng = float(match.group(1)), float(match.group(2))
                # Validate it's Mexico City coordinates
                if 19.0 < lat < 20.0 and -99.5 < lng < -98.5:
                    return lat, lng
        
        return None
    
    def _parse_float(self, text: str) -> Optional[float]:
        """Extract float from text"""
        try:
            # Remove common separators and units
            cleaned = re.sub(r'[^\d.]', '', text)
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None
    
    def _parse_int(self, text: str) -> Optional[int]:
        """Extract integer from text"""
        try:
            match = re.search(r'\d+', text)
            if match:
                return int(match.group(0))
        except:
            pass
        return None


def test_analyzer():
    """Test the analyzer with sample URLs"""
    analyzer = URLAnalyzer()
    
    # Test URLs (replace with real ones for testing)
    test_urls = [
        "https://www.lamudi.com.mx/...",
        "https://inmuebles.mercadolibre.com.mx/...",
        "https://www.inmuebles24.com/...",
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        try:
            data = analyzer.analyze_url(url)
            if data:
                print(json.dumps(data.to_dict(), indent=2, ensure_ascii=False))
            else:
                print("❌ Failed to extract data")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_analyzer()
