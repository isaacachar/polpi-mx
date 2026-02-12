#!/usr/bin/env python3
"""Test if MercadoLibre has a JSON API we can use"""

import requests
import json

# Try common API endpoints
api_urls = [
    # V1 API
    "https://api.mercadolibre.com/sites/MLM/search?category=MLM1459&state=TUxNUERGRg&limit=50",
    # Real estate category in CDMX
    "https://api.mercadolibre.com/sites/MLM/search?category=MLM1459&state_name=Distrito%20Federal&limit=50",
    # Apartments for sale
    "https://api.mercadolibre.com/sites/MLM/search?category=MLM50262&state=TUxNUERGRg&limit=50",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

for i, url in enumerate(api_urls, 1):
    print(f"\n{i}. Testing: {url[:80]}...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✓ Got JSON response")
                print(f"   Keys: {list(data.keys())[:10]}")
                
                if 'results' in data:
                    print(f"   Results: {len(data.get('results', []))} items")
                    
                    if data['results']:
                        # Print first result structure
                        first = data['results'][0]
                        print(f"   Sample item keys: {list(first.keys())[:15]}")
                        print(f"   Title: {first.get('title', 'N/A')[:60]}")
                        print(f"   Price: {first.get('price', 'N/A')}")
                        
                        # Save sample
                        with open('/Users/isaachomefolder/Desktop/polpi-mx/data/ml_api_sample.json', 'w') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        print(f"   ✓ Saved to data/ml_api_sample.json")
                        break
            except:
                print(f"   ✗ Not JSON")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\nDone!")
