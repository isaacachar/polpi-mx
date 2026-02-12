#!/usr/bin/env python3
"""Test accessibility of Mexican real estate portals"""

import requests
import time

def test_portal(name, url):
    """Test if a portal is accessible"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
    }
    
    try:
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Check for common blocking indicators
        is_blocked = False
        blocking_reason = None
        
        if response.status_code == 403:
            is_blocked = True
            blocking_reason = "403 Forbidden"
        elif response.status_code == 503:
            is_blocked = True
            blocking_reason = "503 Service Unavailable"
        elif 'cloudflare' in response.text.lower() and 'challenge' in response.text.lower():
            is_blocked = True
            blocking_reason = "Cloudflare Challenge"
        elif 'captcha' in response.text.lower():
            is_blocked = True
            blocking_reason = "CAPTCHA detected"
        elif len(response.content) < 1000:
            is_blocked = True
            blocking_reason = "Suspiciously small response"
        
        if is_blocked:
            print(f"   ❌ BLOCKED: {blocking_reason}")
            print(f"   Status: {response.status_code}")
            return False, blocking_reason
        else:
            print(f"   ✅ ACCESSIBLE")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.content):,} bytes")
            return True, None
            
    except requests.exceptions.Timeout:
        print(f"   ⚠️ TIMEOUT")
        return False, "Timeout"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, str(e)

def main():
    print("🌐 Testing Mexican Real Estate Portals")
    print("=" * 60)
    
    portals = [
        ("PropiedadesMX", "https://propiedades.com/ciudad-de-mexico/venta"),
        ("Metros Cúbicos", "https://www.metroscubicos.com/inmuebles/venta/departamento/distrito-federal/"),
        ("Icasa", "https://www.icasas.mx/venta/casas/distrito-federal"),
        ("Segundamano", "https://www.segundamano.mx/distrito-federal/inmuebles"),
        ("Century 21 Mexico", "https://www.century21mexico.com/resultados-propiedades?state=ciudad-de-mexico"),
    ]
    
    results = {}
    
    for name, url in portals:
        accessible, reason = test_portal(name, url)
        results[name] = {
            'accessible': accessible,
            'reason': reason,
            'url': url
        }
        time.sleep(2)  # Be polite
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    accessible_portals = [name for name, data in results.items() if data['accessible']]
    blocked_portals = [name for name, data in results.items() if not data['accessible']]
    
    if accessible_portals:
        print(f"\n✅ ACCESSIBLE ({len(accessible_portals)}):")
        for name in accessible_portals:
            print(f"   • {name}")
    
    if blocked_portals:
        print(f"\n❌ BLOCKED ({len(blocked_portals)}):")
        for name in blocked_portals:
            reason = results[name]['reason']
            print(f"   • {name} - {reason}")
    
    print(f"\nResult: {len(accessible_portals)}/{len(portals)} portals accessible")
    
    return results

if __name__ == '__main__':
    main()
