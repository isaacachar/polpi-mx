#!/usr/bin/env python3
"""Quick test of MercadoLibre Selenium scraper"""

import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

print("🔧 Testing MercadoLibre Selenium scraper...")
print("=" * 60)

# Setup Chrome
print("\n1. Setting up Chrome...")
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
print("   ✓ Chrome initialized")

try:
    # Test URL
    url = "https://inmuebles.mercadolibre.com.mx/departamentos/venta/distrito-federal/"
    print(f"\n2. Loading URL: {url}")
    driver.get(url)
    print("   ✓ Page loaded")
    
    # Wait for JavaScript
    time.sleep(3)
    print("   ✓ Waited for JavaScript")
    
    # Extract preloaded state
    print("\n3. Extracting window.__PRELOADED_STATE__...")
    script = "return window.__PRELOADED_STATE__ || window.__PRELOADED_STATES__ || null;"
    preloaded_state = driver.execute_script(script)
    
    if preloaded_state:
        print(f"   ✓ Found preloaded state!")
        print(f"   Keys: {list(preloaded_state.keys())[:10]}")
        
        # Save to file
        with open('/Users/isaachomefolder/Desktop/polpi-mx/data/test_preloaded_state.json', 'w') as f:
            json.dump(preloaded_state, f, indent=2, ensure_ascii=False)
        print("   ✓ Saved to data/test_preloaded_state.json")
        
        # Try to find results
        print("\n4. Looking for results...")
        results = None
        
        if 'results' in preloaded_state:
            results = preloaded_state['results']
            print(f"   ✓ Found 'results' key with {len(results) if isinstance(results, list) else 0} items")
        
        if 'items' in preloaded_state:
            items = preloaded_state['items']
            print(f"   ✓ Found 'items' key with {len(items) if isinstance(items, list) else 0} items")
        
        # Check nested structure
        for key in preloaded_state.keys():
            if isinstance(preloaded_state[key], dict):
                if 'results' in preloaded_state[key]:
                    nested_results = preloaded_state[key]['results']
                    print(f"   ✓ Found 'results' in '{key}' with {len(nested_results) if isinstance(nested_results, list) else 0} items")
                if 'items' in preloaded_state[key]:
                    nested_items = preloaded_state[key]['items']
                    print(f"   ✓ Found 'items' in '{key}' with {len(nested_items) if isinstance(nested_items, list) else 0} items")
        
        print("\n✅ TEST SUCCESSFUL - Check data/test_preloaded_state.json for full data")
    else:
        print("   ✗ No preloaded state found!")
        print("   Trying alternative approaches...")
        
        # Check page source
        if "__PRELOADED_STATE__" in driver.page_source:
            print("   ✓ Found __PRELOADED_STATE__ in page source (but couldn't extract)")
        else:
            print("   ✗ __PRELOADED_STATE__ not in page source at all")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n5. Closing browser...")
    driver.quit()
    print("   ✓ Done")
    print("=" * 60)
