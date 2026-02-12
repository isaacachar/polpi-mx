#!/usr/bin/env python3
"""Save MercadoLibre page source for inspection"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

print("📄 Saving MercadoLibre page source...")

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = "https://inmuebles.mercadolibre.com.mx/departamentos/venta/distrito-federal/"
    print(f"Loading: {url}")
    driver.get(url)
    
    # Wait progressively
    for i in range(1, 8):
        time.sleep(1)
        page_source = driver.page_source
        filename = f"/Users/isaachomefolder/Desktop/polpi-mx/data/ml_page_source_{i}s.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"  {i}s: Saved {len(page_source)} bytes to ml_page_source_{i}s.html")
        
        # Check if we have results
        if 'ui-search-layout__item' in page_source:
            print(f"  ✓ Found search results at {i}s!")
        if 'window.__' in page_source:
            print(f"  ✓ Found window.__ objects at {i}s!")

except Exception as e:
    print(f"ERROR: {e}")

finally:
    driver.quit()
    print("Done!")
