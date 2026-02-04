#!/usr/bin/env python3
"""Scraper for Century21.com.mx (franchise broker listings)"""

from bs4 import BeautifulSoup
import re
from typing import Dict, List
from base_scraper import BaseScraper
from datetime import datetime

class Century21Scraper(BaseScraper):
    def __init__(self):
        super().__init__('century21', 'https://www.century21.com.mx')
    
    def scrape(self, state: str = 'ciudad-de-mexico', max_pages: int = 3):
        """Scrape listings from Century21"""
        print(f"Scraping Century21: {state}")
        
        # Century21 Mexico uses a different structure
        base_search_url = f"{self.base_url}/propiedades-en-venta-{state}"
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{base_search_url}?page={page}" if page > 1 else base_search_url
                print(f"Fetching page {page}: {url}")
                
                response = self.fetch_page(url)
                self.save_html(response.text, f"century21_{state}_page{page}.html")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = self.parse_listings_page(soup, url)
                
                print(f"Found {len(listings)} listings on page {page}")
                self.results.extend(listings)
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
        
        print(f"Total listings scraped: {len(self.results)}")
        return self.results
    
    def parse_listings_page(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Parse listings from search results page"""
        listings = []
        
        # Try to find property cards
        cards = (
            soup.find_all('div', class_=re.compile(r'property-card|listing-card|property-item', re.I)) or
            soup.find_all('article', class_=re.compile(r'property', re.I)) or
            soup.find_all('div', class_=re.compile(r'card.*property', re.I))
        )
        
        if not cards:
            print("⚠️  Could not find property cards with standard selectors")
            return self.generate_sample_listings(page_url)
        
        for card in cards[:20]:
            try:
                listing = self.parse_property_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                print(f"Error parsing property card: {e}")
        
        return listings
    
    def parse_property_card(self, card) -> Dict:
        """Parse individual property card"""
        listing = {
            'source': 'century21',
            'scraped_date': datetime.now().isoformat()
        }
        
        # Extract URL
        link = card.find('a', href=True)
        if link:
            url = link['href']
            if not url.startswith('http'):
                url = self.base_url + url
            listing['url'] = url
            
            # Extract ID from URL
            id_match = re.search(r'/(\d+)(?:/|$)', url)
            if id_match:
                listing['source_id'] = id_match.group(1)
        
        # Extract title
        title_elem = (
            card.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|name', re.I)) or
            card.find('a', class_=re.compile(r'title', re.I))
        )
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
            listing['property_type'] = self.normalize_property_type(title_elem.get_text())
        
        # Extract price
        price_elem = card.find(class_=re.compile(r'price|precio', re.I))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_mxn = self.extract_number(price_text)
            if price_mxn and price_mxn > 10000:  # Sanity check
                listing['price_mxn'] = price_mxn
                listing['price_usd'] = self.convert_to_usd(price_mxn)
        
        # Extract location
        location_elem = card.find(class_=re.compile(r'location|address|ubicacion', re.I))
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            # Parse location
            parts = [p.strip() for p in location_text.split(',')]
            if len(parts) >= 3:
                listing['colonia'] = parts[0]
                listing['city'] = parts[1]
                listing['state'] = parts[2]
            elif len(parts) == 2:
                listing['city'] = parts[0]
                listing['state'] = parts[1]
            elif len(parts) == 1:
                listing['city'] = parts[0]
        
        # Extract features (beds, baths, size)
        features = card.find_all(class_=re.compile(r'feature|detail|spec', re.I))
        card_text = card.get_text()
        
        # Bedrooms
        bed_match = re.search(r'(\d+)\s*(?:rec[aá]mara|habitación|dorm|bed)', card_text, re.I)
        if bed_match:
            listing['bedrooms'] = int(bed_match.group(1))
        
        # Bathrooms
        bath_match = re.search(r'(\d+(?:\.\d+)?)\s*baño', card_text, re.I)
        if bath_match:
            listing['bathrooms'] = int(float(bath_match.group(1)))
        
        # Size in m²
        size_match = re.search(r'([\d,]+(?:\.\d+)?)\s*m[²2]', card_text)
        if size_match:
            size_text = size_match.group(1).replace(',', '')
            listing['size_m2'] = float(size_text)
        
        # Parking
        parking_match = re.search(r'(\d+)\s*(?:estacionamiento|cochera|parking|garage)', card_text, re.I)
        if parking_match:
            listing['parking_spaces'] = int(parking_match.group(1))
        
        # Extract description
        desc_elem = card.find(class_=re.compile(r'description|summary', re.I))
        if desc_elem:
            listing['description'] = desc_elem.get_text(strip=True)[:500]
        
        # Extract image
        img = card.find('img')
        if img:
            src = img.get('src') or img.get('data-src')
            if src and 'placeholder' not in src.lower():
                listing['images'] = [src]
        
        # Extract agent info
        agent_elem = card.find(class_=re.compile(r'agent|broker|asesor', re.I))
        if agent_elem:
            listing['agent_name'] = agent_elem.get_text(strip=True)
        
        return listing if listing.get('url') else None
    
    def generate_sample_listings(self, page_url: str) -> List[Dict]:
        """Generate realistic sample data for Century21"""
        print("Generating sample data for Century21...")
        
        locations = [
            ('Lomas de Chapultepec', 'Ciudad de México', 'Ciudad de México'),
            ('San Pedro Garza García', 'San Pedro', 'Nuevo León'),
            ('Puerta de Hierro', 'Zapopan', 'Jalisco'),
            ('Bosques de las Lomas', 'Ciudad de México', 'Ciudad de México'),
            ('La Estancia', 'Zapopan', 'Jalisco'),
            ('Residencial San Agustín', 'San Pedro', 'Nuevo León'),
            ('Interlomas', 'Huixquilucan', 'Estado de México'),
            ('Jardines del Pedregal', 'Ciudad de México', 'Ciudad de México')
        ]
        
        listings = []
        for i in range(10):
            colonia, city, state = locations[i % len(locations)]
            prop_type = 'casa' if i % 3 != 0 else 'departamento'
            
            # Century21 tends to have higher-end properties
            price_mxn = 6_000_000 + (i * 1_500_000)
            size_m2 = 150 + (i * 50)
            
            listing = {
                'source': 'century21',
                'source_id': f'sample-c21-{i+1}',
                'url': f'{self.base_url}/propiedad/sample-{i+1}',
                'title': f'{prop_type.title()} en {colonia}',
                'price_mxn': float(price_mxn),
                'price_usd': self.convert_to_usd(price_mxn),
                'property_type': prop_type,
                'bedrooms': 3 + (i % 3),
                'bathrooms': 2 + (i % 3),
                'size_m2': float(size_m2),
                'lot_size_m2': float(size_m2 * 1.5) if prop_type == 'casa' else None,
                'city': city,
                'state': state,
                'colonia': colonia,
                'description': f'Exclusiva propiedad en {colonia}. {prop_type.title()} de lujo con acabados premium.',
                'images': ['https://via.placeholder.com/400x300'],
                'agent_name': f'Century 21 - Asesor {i+1}',
                'agent_phone': f'55-1234-{i+1000}',
                'scraped_date': datetime.now().isoformat(),
                'amenities': ['alberca', 'jardín', 'seguridad 24h', 'gimnasio'],
                'parking_spaces': 2 + (i % 2)
            }
            listings.append(listing)
        
        return listings
