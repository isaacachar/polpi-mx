#!/usr/bin/env python3
"""
Simplified RE/MAX scraper - focuses on getting WORKING results with images
Uses a more reliable approach by checking network requests
"""

import sys
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

class RemaxSimpleScraper:
    def __init__(self):
        self.db = PolpiDB()
        self.inserted = 0
        self.errors = 0
        
    def init_driver(self):
        """Initialize Chrome with network logging"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Enable performance logging to capture network requests
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        self.driver = webdriver.Chrome(options=options)
        
    def extract_price(self, text):
        """Extract price from text"""
        if not text:
            return None
        text = text.replace(',', '').replace('$', '').replace(' ', '')
        match = re.search(r'(\d+(?:\.\d+)?)', text)
        if match:
            price = float(match.group(1))
            if price < 10000:  # Likely in millions
                price *= 1_000_000
            return price
        return None
    
    def scrape_from_api(self):
        """
        Alternative approach: Try to find and use RE/MAX's internal API
        by monitoring network requests when loading the search page
        """
        print("=" * 60)
        print("RE/MAX Simple Scraper - API Approach")
        print("=" * 60)
        
        try:
            self.init_driver()
            
            # Load search page and capture network traffic
            url = 'https://remax.com.mx/propiedades/ciudad+de+mexico_ciudad+de+mexico/venta'
            print(f"\nLoading: {url}")
            print("Monitoring network requests for API calls...")
            
            self.driver.get(url)
            time.sleep(10)  # Wait for all API calls to complete
            
            # Scroll to trigger more loading
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)
            
            # Get performance logs (network requests)
            logs = self.driver.get_log('performance')
            
            api_urls = []
            for entry in logs:
                try:
                    log_data = json.loads(entry['message'])
                    if 'message' in log_data and 'params' in log_data['message']:
                        params = log_data['message']['params']
                        if 'request' in params:
                            request_url = params['request'].get('url', '')
                            # Look for API endpoints
                            if 'api' in request_url.lower() or 'search' in request_url or 'propiedad' in request_url:
                                if request_url not in api_urls:
                                    api_urls.append(request_url)
                                    print(f"  Found API: {request_url[:100]}...")
                except:
                    continue
            
            if api_urls:
                print(f"\n✓ Found {len(api_urls)} potential API endpoints")
                print("\n📝 Manual next steps:")
                print("1. Inspect these API URLs to find the property data endpoint")
                print("2. Modify scraper to call API directly")
                for i, url in enumerate(api_urls[:5], 1):
                    print(f"   {i}. {url}")
            else:
                print("\n⚠ No obvious API endpoints found")
                print("RE/MAX uses complex JS rendering - consider alternatives:")
                print("  - Use Inmuebles24 (already working)")
                print("  - Try Vivanuncios")
                print("  - Focus on Sotheby's for luxury + images")
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    scraper = RemaxSimpleScraper()
    scraper.scrape_from_api()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    print("RE/MAX site is heavily JS-rendered and difficult to scrape.")
    print("Better alternatives for high-quality CDMX listings:")
    print("  1. Inmuebles24 (easier to scrape)")
    print("  2. Vivanuncios")
    print("  3. Sotheby's (luxury, great photos - focus here!)")
    print("  4. Century 21 Mexico")
    print("=" * 60)

if __name__ == '__main__':
    main()
