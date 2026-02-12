#!/usr/bin/env python3
"""Test script to verify Inmuebles24 access"""

import cloudscraper

print("Creating scraper...")
scraper = cloudscraper.create_scraper()

url = "https://www.inmuebles24.com/departamentos-en-venta-en-ciudad-de-mexico.html"
print(f"Fetching: {url}")

try:
    response = scraper.get(url, timeout=30)
    print(f"Status code: {response.status_code}")
    print(f"Response length: {len(response.text)} chars")
    print(f"First 500 chars: {response.text[:500]}")
    
    if "Cloudflare" in response.text:
        print("\n⚠️  CLOUDFLARE DETECTED")
    else:
        print("\n✅ SUCCESS - No Cloudflare block detected")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
