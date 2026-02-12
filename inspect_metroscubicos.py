#!/usr/bin/env python3
"""Inspect MetrosCubicos structure"""

import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-MX,es;q=0.9',
}

print("🔍 Inspecting MetrosCubicos.com...")

response = requests.get("https://www.metroscubicos.com/", headers=headers, timeout=15)
soup = BeautifulSoup(response.text, 'html.parser')

# Save HTML for inspection
with open('/Users/isaachomefolder/Desktop/polpi-mx/data/metroscubicos_sample.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"\n✅ HTML saved to data/metroscubicos_sample.html")
print(f"   Size: {len(response.content):,} bytes\n")

# Look for JSON-LD data
print("📋 Looking for JSON-LD structured data...")
json_scripts = soup.find_all('script', type='application/ld+json')
print(f"   Found {len(json_scripts)} JSON-LD scripts")

for i, script in enumerate(json_scripts):
    try:
        data = json.loads(script.string)
        print(f"\n   Script {i+1}: {data.get('@type', 'Unknown type')}")
        if isinstance(data, list):
            print(f"      List with {len(data)} items")
        else:
            print(f"      Keys: {list(data.keys())[:10]}")
    except:
        print(f"   Script {i+1}: Not valid JSON")

# Look for property listings in HTML
print("\n🏠 Looking for property listing patterns...")

# Pattern 1: Links with /inmueble/
inmueble_links = soup.find_all('a', href=lambda x: x and '/inmueble/' in x if x else False)
print(f"   Links with '/inmueble/': {len(inmueble_links)}")
if inmueble_links:
    print(f"   Sample: {inmueble_links[0].get('href')}")

# Pattern 2: Divs/articles with property class
property_divs = soup.find_all(['div', 'article'], class_=lambda x: x and ('property' in x.lower() or 'listing' in x.lower()) if x else False)
print(f"   Property divs/articles: {len(property_divs)}")

# Pattern 3: Look for search/filter URLs
print("\n🔍 Looking for search/filter URLs...")
cdmx_links = [a for a in soup.find_all('a', href=True) if any(term in a.get('href', '').lower() for term in ['cdmx', 'ciudad', 'mexico', 'distrito'])]
if cdmx_links:
    print(f"   Found {len(cdmx_links)} CDMX-related links:")
    for link in cdmx_links[:5]:
        print(f"      • {link.get('href')}")

# Pattern 4: Look for data attributes
print("\n📊 Looking for data attributes...")
data_elements = soup.find_all(attrs=lambda x: any(k.startswith('data-') for k in x.keys()) if x else False)
print(f"   Elements with data- attributes: {len(data_elements)}")
if data_elements:
    sample = data_elements[0]
    data_attrs = {k: v for k, v in sample.attrs.items() if k.startswith('data-')}
    print(f"   Sample data attributes: {list(data_attrs.keys())[:5]}")

print("\n✅ Inspection complete!")
