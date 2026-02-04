#!/usr/bin/env python3
"""Base scraper class with common functionality"""

import requests
import time
import random
import json
from typing import Dict, List
from datetime import datetime
import os

class BaseScraper:
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        self.results = []
        self.errors = []
    
    def get_headers(self) -> Dict:
        """Get random headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def fetch_page(self, url: str, max_retries: int = 3) -> requests.Response:
        """Fetch a page with retry logic"""
        for attempt in range(max_retries):
            try:
                # Add delay to respect rate limits
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    timeout=30
                )
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    self.errors.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    raise
                time.sleep(random.uniform(2, 5))
    
    def save_raw_data(self, data: Dict, filename: str):
        """Save raw scraped data for debugging"""
        os.makedirs('data/raw', exist_ok=True)
        filepath = f'data/raw/{self.name}_{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_html(self, html: str, filename: str):
        """Save raw HTML for debugging"""
        os.makedirs('data/html', exist_ok=True)
        filepath = f'data/html/{self.name}_{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def normalize_property_type(self, raw_type: str) -> str:
        """Normalize property type to standard values"""
        raw_type = raw_type.lower()
        
        if any(word in raw_type for word in ['casa', 'residencia', 'villa', 'chalet']):
            return 'casa'
        elif any(word in raw_type for word in ['departamento', 'depto', 'apartamento', 'piso']):
            return 'departamento'
        elif any(word in raw_type for word in ['terreno', 'lote', 'solar']):
            return 'terreno'
        elif any(word in raw_type for word in ['oficina', 'consultorio']):
            return 'oficina'
        elif any(word in raw_type for word in ['bodega', 'nave', 'almacén']):
            return 'bodega'
        elif any(word in raw_type for word in ['local', 'comercial']):
            return 'local_comercial'
        else:
            return 'otro'
    
    def extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        if not text:
            return None
        
        # Remove common currency symbols and text
        text = text.replace('$', '').replace(',', '').replace('MXN', '').replace('USD', '')
        text = text.replace('m²', '').replace('m2', '').strip()
        
        # Extract first number found
        import re
        match = re.search(r'[\d.]+', text)
        if match:
            try:
                return float(match.group())
            except:
                return None
        return None
    
    def convert_to_usd(self, price_mxn: float, rate: float = 17.0) -> float:
        """Convert MXN to USD (using approximate rate)"""
        if not price_mxn:
            return None
        return round(price_mxn / rate, 2)
    
    def get_results(self) -> List[Dict]:
        """Get all scraped results"""
        return self.results
    
    def get_errors(self) -> List[Dict]:
        """Get all errors encountered"""
        return self.errors
    
    def scrape(self, **kwargs):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement scrape()")
