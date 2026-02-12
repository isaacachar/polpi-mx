#!/usr/bin/env python3
"""Quick test to check MercadoLibre page structure"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.page_load_strategy = 'none'

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

url = 'https://inmuebles.mercadolibre.com.mx/departamentos/venta/distrito-federal/'
print(f"Loading: {url}")
driver.get(url)

# Wait for page to start loading
time.sleep(8)

# Check for various possible objects
scripts_to_try = [
    "return typeof window.__PRELOADED_STATE__;",
    "return typeof window.__PRELOADED_STATES__;",
    "return typeof window.__NEXT_DATA__;",
    "return typeof window.__INITIAL_STATE__;",
    "return Object.keys(window).filter(k => k.includes('STATE') || k.includes('DATA')).join(', ');",
]

print("\nChecking for JavaScript objects...")
for script in scripts_to_try:
    try:
        result = driver.execute_script(script)
        print(f"  {script.split('return ')[1][:50]}... = {result}")
    except Exception as e:
        print(f"  Error: {e}")

# Get page source snippet
page_source = driver.page_source
print(f"\nPage source length: {len(page_source)} chars")

# Look for script tags with JSON
import re
scripts = re.findall(r'<script[^>]*>(.*?)</script>', page_source[:50000], re.DOTALL)
print(f"Found {len(scripts)} script tags")

# Look for specific patterns
if '__PRELOADED_STATE__' in page_source:
    print("✓ Found __PRELOADED_STATE__ in page source")
else:
    print("✗ No __PRELOADED_STATE__ in page source")

if '__NEXT_DATA__' in page_source:
    print("✓ Found __NEXT_DATA__ in page source")
else:
    print("✗ No __NEXT_DATA__ in page source")

# Save page source for inspection
with open('/Users/isaachomefolder/Desktop/polpi-mx/data/ml_test_page.html', 'w') as f:
    f.write(page_source)
print("\n✓ Saved page source to data/ml_test_page.html")

driver.quit()
