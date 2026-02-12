#!/usr/bin/env python3
"""Quick test of MercadoLibre accessibility"""

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-MX,es;q=0.9',
}

urls = [
    "https://inmuebles.mercadolibre.com.mx/departamentos/venta/ciudad-de-mexico/",
    "https://www.mercadolibre.com.mx/",
]

for url in urls:
    print(f"\n🔍 Testing: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {response.status_code}")
        print(f"   Size: {len(response.content):,} bytes")
        print(f"   Final URL: {response.url}")
        
        # Check for blocks
        if 'captcha' in response.text.lower():
            print(f"   ⚠️  CAPTCHA detected")
        elif 'cloudflare' in response.text.lower():
            print(f"   ⚠️  Cloudflare detected")
        else:
            print(f"   ✅ Looks accessible")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
