#!/usr/bin/env python3
"""Populate database with sample data for testing"""

from database import PolpiDB
from datetime import datetime
import random

def generate_sample_listings():
    """Generate realistic sample listings for major Mexican cities"""
    
    db = PolpiDB()
    
    print("🐙 Polpi MX - Generating Sample Data")
    print("=" * 60)
    
    # Major Mexican cities and colonias
    locations = [
        # CDMX
        ("Ciudad de México", "Ciudad de México", "Polanco", 19.4338, -99.1947),
        ("Ciudad de México", "Ciudad de México", "Roma Norte", 19.4170, -99.1623),
        ("Ciudad de México", "Ciudad de México", "Condesa", 19.4115, -99.1719),
        ("Ciudad de México", "Ciudad de México", "Santa Fe", 19.3663, -99.2663),
        ("Ciudad de México", "Ciudad de México", "Del Valle", 19.3751, -99.1690),
        ("Ciudad de México", "Ciudad de México", "Coyoacán Centro", 19.3467, -99.1632),
        ("Ciudad de México", "Ciudad de México", "Narvarte", 19.3917, -99.1546),
        ("Ciudad de México", "Ciudad de México", "San Ángel", 19.3474, -99.1907),
        ("Ciudad de México", "Ciudad de México", "Lindavista", 19.4900, -99.1277),
        ("Ciudad de México", "Ciudad de México", "Lomas de Chapultepec", 19.4260, -99.2082),
        
        # Monterrey
        ("Nuevo León", "Monterrey", "San Pedro Garza García", 25.6515, -100.3606),
        ("Nuevo León", "Monterrey", "Valle Oriente", 25.6629, -100.2837),
        ("Nuevo León", "Monterrey", "Centro", 25.6714, -100.3089),
        ("Nuevo León", "Monterrey", "Residencial San Agustín", 25.6583, -100.3653),
        
        # Guadalajara
        ("Jalisco", "Guadalajara", "Providencia", 20.6797, -103.3773),
        ("Jalisco", "Guadalajara", "Puerta de Hierro", 20.6515, -103.4236),
        ("Jalisco", "Zapopan", "La Estancia", 20.6734, -103.4441),
        ("Jalisco", "Zapopan", "Zapopan Centro", 20.7217, -103.3927),
        
        # Querétaro
        ("Querétaro", "Querétaro", "Juriquilla", 20.6436, -100.4471),
        ("Querétaro", "Querétaro", "Centro Histórico", 20.5888, -100.3899),
        
        # Puebla
        ("Puebla", "Puebla", "Angelópolis", 19.0176, -98.2755),
        ("Puebla", "Puebla", "Centro Histórico", 19.0414, -98.2063),
        
        # Estado de México
        ("Estado de México", "Naucalpan", "Satellite", 19.5082, -99.2341),
        ("Estado de México", "Huixquilucan", "Interlomas", 19.3926, -99.2918),
    ]
    
    property_types = ["departamento", "casa", "departamento", "casa", "terreno"]
    sources = ["inmuebles24", "vivanuncios", "century21"]
    
    # Generate 50 listings
    listings_generated = 0
    
    for i in range(50):
        state, city, colonia, lat, lng = random.choice(locations)
        prop_type = random.choice(property_types)
        source = random.choice(sources)
        
        # Realistic price ranges by city
        if city == "Ciudad de México" and colonia in ["Polanco", "Lomas de Chapultepec", "Santa Fe"]:
            base_price = random.randint(5_000_000, 15_000_000)
        elif city == "San Pedro Garza García":
            base_price = random.randint(4_000_000, 12_000_000)
        elif city in ["Monterrey", "Guadalajara"]:
            base_price = random.randint(2_500_000, 8_000_000)
        else:
            base_price = random.randint(1_500_000, 6_000_000)
        
        # Property type multipliers
        if prop_type == "casa":
            price_mxn = base_price * random.uniform(1.2, 2.0)
            size_m2 = random.randint(120, 350)
            lot_size_m2 = size_m2 * random.uniform(1.5, 3.0)
        elif prop_type == "terreno":
            price_mxn = base_price * random.uniform(0.5, 1.5)
            size_m2 = random.randint(200, 1000)
            lot_size_m2 = size_m2
        else:  # departamento
            price_mxn = base_price * random.uniform(0.7, 1.3)
            size_m2 = random.randint(60, 180)
            lot_size_m2 = None
        
        bedrooms = random.randint(1, 5) if prop_type != "terreno" else None
        bathrooms = random.randint(1, 4) if prop_type != "terreno" else None
        parking_spaces = random.randint(1, 3) if prop_type != "terreno" else None
        
        amenities = []
        if prop_type == "casa":
            amenities = random.sample(["jardín", "alberca", "terraza", "seguridad 24h", "gimnasio"], k=random.randint(2, 4))
        elif prop_type == "departamento":
            amenities = random.sample(["elevador", "seguridad 24h", "gimnasio", "estacionamiento techado", "área común"], k=random.randint(2, 3))
        
        listing = {
            "source": source,
            "source_id": f"sample-{source}-{i+1}",
            "url": f"https://{source}.com.mx/propiedad/{i+1}",
            "title": f"{prop_type.title()} en {colonia}",
            "price_mxn": float(round(price_mxn, 2)),
            "price_usd": float(round(price_mxn / 17.0, 2)),
            "property_type": prop_type,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "size_m2": float(round(size_m2, 2)),
            "lot_size_m2": float(round(lot_size_m2, 2)) if lot_size_m2 else None,
            "state": state,
            "city": city,
            "colonia": colonia,
            "lat": lat + random.uniform(-0.01, 0.01),
            "lng": lng + random.uniform(-0.01, 0.01),
            "description": f"Hermoso {prop_type} ubicado en {colonia}, {city}. Excelente ubicación cerca de todos los servicios.",
            "images": [f"https://via.placeholder.com/800x600?text={prop_type.title()}+{i+1}"],
            "agent_name": f"Inmobiliaria {random.choice(['Premium', 'Elite', 'Gold', 'Top', 'Select'])} - Agente {random.randint(1, 50)}",
            "agent_phone": f"55-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "amenities": amenities,
            "parking_spaces": parking_spaces,
        }
        
        try:
            listing_id = db.insert_listing(listing)
            listings_generated += 1
            if (listings_generated) % 10 == 0:
                print(f"✓ Generated {listings_generated} listings...")
        except Exception as e:
            print(f"✗ Error inserting listing: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully generated {listings_generated} sample listings")
    
    # Print statistics
    stats = db.get_stats()
    print("\nDATABASE STATISTICS")
    print("=" * 60)
    print(f"Total listings: {stats['total_listings']}")
    print(f"Cities: {stats['cities']}")
    print(f"Colonias: {stats['colonias']}")
    print(f"\nListings by source:")
    for source, count in stats['sources'].items():
        print(f"  - {source}: {count}")
    
    print("\n✅ Database ready! Run: python3 api_server.py")

if __name__ == '__main__':
    generate_sample_listings()
