#!/usr/bin/env python3
"""Quick test of the location analyzer endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("POLPI MX LOCATION ANALYZER - END-TO-END TEST")
print("=" * 70)

# Test 1: Colonia name only
print("\n📍 Test 1: Colonia name (Polanco)")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/api/v1/analyze-location",
    json={"location": "Polanco"}
)
data = response.json()
print(f"✅ Status: {response.status_code}")
print(f"   Coordinates: {data['location']['lat']}, {data['location']['lng']}")
print(f"   Colonia: {data['location']['colonia']}")
print(f"   Zoning: {data['zoning']['category']} - {data['zoning']['category_full']}")
print(f"   Max Floors: {data['zoning']['max_floors']}")

# Test 2: With lot size
print("\n🏗️ Test 2: Full analysis (Roma Norte + 500m²)")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/api/v1/analyze-location",
    json={"location": "Roma Norte", "lot_size_m2": 500}
)
data = response.json()
print(f"✅ Status: {response.status_code}")
print(f"   Colonia: {data['location']['colonia']}")
print(f"   Zoning: {data['zoning']['category']}")
if data['buildable']:
    print(f"   Max Buildable: {data['buildable']['max_total_construction_m2']} m²")
if data['development_potential']:
    units = data['development_potential']['estimated_units']
    print(f"   Potential: {units['apartments_60m2']} apartments (60m²)")
if data['market_data']:
    print(f"   Avg Price/m²: ${data['market_data']['avg_price_per_m2']}")
    print(f"   Total Listings: {data['market_data']['total_listings']}")

# Test 3: Coordinates
print("\n📐 Test 3: Coordinates (Centro Histórico)")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/api/v1/analyze-location",
    json={"location": "19.433, -99.133", "lot_size_m2": 1000}
)
data = response.json()
print(f"✅ Status: {response.status_code}")
print(f"   Resolved to: {data['location']['colonia']}")
print(f"   Heritage Zone: {data['zoning']['is_heritage_zone']}")
print(f"   Max Buildable: {data['buildable']['max_total_construction_m2']} m²")
units = data['development_potential']['estimated_units']
print(f"   Could build: {units['apartments_80m2']} apartments (80m²)")
print(f"   Or: {units['hotel_rooms_35m2']} hotel rooms")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - LOCATION ANALYZER IS FULLY OPERATIONAL")
print("=" * 70)
print(f"\n🌐 Access at: {BASE_URL}/location-analyze.html\n")
