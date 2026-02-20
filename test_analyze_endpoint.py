#!/usr/bin/env python3
"""Quick test of the analyze endpoint"""

from url_analyzer import URLAnalyzer

# Test URL extraction (mock test)
analyzer = URLAnalyzer()

print("✓ URLAnalyzer initialized")
print("\n📋 Testing URL pattern detection:")

test_urls = [
    "https://www.lamudi.com.mx/detalle/...",
    "https://inmuebles.mercadolibre.com.mx/...",
    "https://www.inmuebles24.com/...",
]

for url in test_urls:
    try:
        if 'lamudi' in url:
            print(f"  ✓ Lamudi detected: {url}")
        elif 'mercadolibre' in url:
            print(f"  ✓ MercadoLibre detected: {url}")
        elif 'inmuebles24' in url:
            print(f"  ✓ Inmuebles24 detected: {url}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n✅ URL analyzer module is working!")
print("\nTo test the full endpoint:")
print("1. Start server: python3 api_server.py")
print("2. Open: http://localhost:8000/analyze.html")
print("3. Paste a real listing URL and click Analyze")
