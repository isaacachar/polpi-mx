#!/usr/bin/env python3
"""Explore accessible portals to find correct listing URLs"""

import requests
from bs4 import BeautifulSoup
import time

def explore_icasas():
    """Explore Icasa to find correct CDMX listings URL"""
    print("\n🔍 Exploring Icasas.mx...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-MX,es;q=0.9',
    }
    
    # Try different URL patterns
    urls_to_try = [
        "https://www.icasas.mx/",
        "https://www.icasas.mx/venta",
        "https://www.icasas.mx/venta/distrito-federal",
        "https://www.icasas.mx/venta/cdmx",
        "https://www.icasas.mx/buscar?location=cdmx",
    ]
    
    for url in urls_to_try:
        try:
            print(f"   Trying: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code} | Size: {len(response.content):,} bytes")
            
            if response.status_code == 200 and len(response.content) > 10000:
                print(f"   ✅ Found working URL!")
                
                # Check if it has listings
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.find_all('a', href=lambda x: x and '/inmueble/' in x)
                print(f"   Found {len(listings)} potential listing links")
                
                if len(listings) > 0:
                    print(f"   Sample URLs:")
                    for listing in listings[:3]:
                        print(f"      • {listing.get('href')}")
                    return url
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def explore_metroscubicos():
    """Explore Metros Cúbicos to find correct CDMX listings URL"""
    print("\n🔍 Exploring MetrosCubicos.com...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-MX,es;q=0.9',
    }
    
    urls_to_try = [
        "https://www.metroscubicos.com/",
        "https://www.metroscubicos.com/inmuebles/venta/",
        "https://www.metroscubicos.com/venta/distrito-federal/",
        "https://www.metroscubicos.com/venta/ciudad-de-mexico/",
        "https://www.metroscubicos.com/cdmx/",
    ]
    
    for url in urls_to_try:
        try:
            print(f"   Trying: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code} | Size: {len(response.content):,} bytes")
            
            if response.status_code == 200 and len(response.content) > 10000:
                print(f"   ✅ Found working URL!")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for common listing patterns
                listings = (
                    soup.find_all('a', href=lambda x: x and '/inmueble' in x if x else False) or
                    soup.find_all('div', class_=lambda x: x and 'property' in x.lower() if x else False)
                )
                print(f"   Found {len(listings)} potential listings")
                
                if len(listings) > 0:
                    return url
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def explore_segundamano():
    """Explore Segundamano to check if still operational"""
    print("\n🔍 Exploring Segundamano.mx...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-MX,es;q=0.9',
    }
    
    urls_to_try = [
        "https://www.segundamano.mx/",
        "https://www.segundamano.mx/inmuebles",
        "https://www.segundamano.mx/anuncios/inmuebles",
    ]
    
    for url in urls_to_try:
        try:
            print(f"   Trying: {url}")
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            print(f"   Status: {response.status_code} | Size: {len(response.content):,} bytes")
            print(f"   Final URL: {response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                print(f"   Page title: {title.string if title else 'N/A'}")
                return url
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def main():
    print("🌐 Exploring Accessible Portals")
    print("=" * 60)
    
    working_urls = {}
    
    # Explore each portal
    icasas_url = explore_icasas()
    if icasas_url:
        working_urls['icasas'] = icasas_url
    
    time.sleep(2)
    
    metros_url = explore_metroscubicos()
    if metros_url:
        working_urls['metroscubicos'] = metros_url
    
    time.sleep(2)
    
    segundamano_url = explore_segundamano()
    if segundamano_url:
        working_urls['segundamano'] = segundamano_url
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 WORKING PORTALS")
    print("=" * 60)
    
    if working_urls:
        for portal, url in working_urls.items():
            print(f"\n✅ {portal.upper()}")
            print(f"   URL: {url}")
    else:
        print("\n❌ No working portals found")
    
    return working_urls

if __name__ == '__main__':
    main()
