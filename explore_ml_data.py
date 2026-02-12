#!/usr/bin/env python3
"""Explore MercadoLibre's actual data structure"""

import sys
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

print("🔍 Exploring MercadoLibre data structure...")
print("=" * 60)

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = "https://inmuebles.mercadolibre.com.mx/departamentos/venta/distrito-federal/"
    print(f"\nLoading: {url}")
    driver.get(url)
    time.sleep(4)
    
    page_source = driver.page_source
    
    # Look for all window.* objects
    print("\n1. Searching for window.* objects in page source...")
    window_objects = re.findall(r'window\.__\w+__', page_source)
    unique_objects = list(set(window_objects))
    print(f"   Found {len(unique_objects)} unique window objects:")
    for obj in unique_objects[:15]:
        print(f"      - {obj}")
    
    # Try to extract these objects
    print("\n2. Trying to extract these objects via JavaScript...")
    for obj_name in unique_objects[:10]:
        try:
            obj = driver.execute_script(f"return {obj_name} || null;")
            if obj:
                print(f"   ✓ {obj_name}: {type(obj).__name__} with {len(obj) if isinstance(obj, (dict, list)) else '?'} items")
                if isinstance(obj, dict):
                    print(f"      Keys: {list(obj.keys())[:10]}")
                    # Save the biggest one
                    if len(obj) > 20:
                        filename = f"/Users/isaachomefolder/Desktop/polpi-mx/data/{obj_name.replace('window.', '').replace('__', '')}.json"
                        with open(filename, 'w') as f:
                            json.dump(obj, f, indent=2, ensure_ascii=False)
                        print(f"      Saved to {filename}")
        except Exception as e:
            print(f"   ✗ {obj_name}: {e}")
    
    # Look for JSON-LD structured data
    print("\n3. Looking for JSON-LD structured data...")
    soup = BeautifulSoup(page_source, 'html.parser')
    json_scripts = soup.find_all('script', type='application/ld+json')
    print(f"   Found {len(json_scripts)} JSON-LD scripts")
    
    for i, script in enumerate(json_scripts[:3]):
        try:
            data = json.loads(script.string)
            print(f"\n   Script {i+1}:")
            if isinstance(data, dict):
                print(f"      Type: {data.get('@type', 'Unknown')}")
                print(f"      Keys: {list(data.keys())[:10]}")
                if data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    print(f"      Items: {len(items)}")
                    if items:
                        print(f"      First item keys: {list(items[0].keys()) if isinstance(items[0], dict) else 'N/A'}")
            elif isinstance(data, list):
                print(f"      List with {len(data)} items")
                if data:
                    print(f"      First item: {type(data[0]).__name__}")
        except:
            pass
    
    # Look for specific data containers
    print("\n4. Looking for data containers in HTML...")
    containers = soup.find_all('div', {'data-item-id': True})
    print(f"   Found {len(containers)} items with data-item-id")
    
    # Look for list items
    items = soup.find_all('li', class_=lambda x: x and 'ui-search-layout__item' in x if x else False)
    print(f"   Found {len(items)} search result items")
    
    if items:
        print("\n   Sample item structure:")
        item = items[0]
        print(f"      Classes: {item.get('class')}")
        
        # Find title
        title = item.find('h2')
        if title:
            print(f"      Title: {title.get_text(strip=True)[:60]}")
        
        # Find price
        price_elem = item.find('span', class_=lambda x: x and 'andes-money-amount' in x if x else False)
        if price_elem:
            print(f"      Price element: {price_elem.get_text(strip=True)[:50]}")
        
        # Find link
        link = item.find('a', href=True)
        if link:
            print(f"      Link: {link['href'][:60]}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n" + "=" * 60)
