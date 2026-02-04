#!/usr/bin/env python3
"""
Generate production-quality realistic data for Polpi MX
Creates 500+ listings with authentic Mexican real estate data
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from database import PolpiDB
import hashlib

class ProductionDataGenerator:
    def __init__(self):
        self.db = PolpiDB()
        
        # CDMX colonias with real coordinates and pricing (MXN/m²)
        self.cities_data = {
            "Ciudad de México": {
                "state": "Ciudad de México",
                "neighborhoods": {
                    "Polanco": {"lat": 19.4338, "lng": -99.1947, "price_range": (45000, 80000)},
                    "Condesa": {"lat": 19.4115, "lng": -99.1719, "price_range": (35000, 55000)},
                    "Roma Norte": {"lat": 19.4170, "lng": -99.1623, "price_range": (30000, 50000)},
                    "Roma Sur": {"lat": 19.4095, "lng": -99.1628, "price_range": (25000, 40000)},
                    "Santa Fe": {"lat": 19.3663, "lng": -99.2663, "price_range": (25000, 45000)},
                    "Coyoacán": {"lat": 19.3467, "lng": -99.1632, "price_range": (20000, 35000)},
                    "Del Valle": {"lat": 19.3751, "lng": -99.1690, "price_range": (25000, 40000)},
                    "Narvarte": {"lat": 19.3917, "lng": -99.1546, "price_range": (18000, 30000)},
                    "Nápoles": {"lat": 19.3857, "lng": -99.1621, "price_range": (20000, 32000)},
                    "San Ángel": {"lat": 19.3474, "lng": -99.1907, "price_range": (30000, 50000)},
                    "Lomas de Chapultepec": {"lat": 19.4260, "lng": -99.2082, "price_range": (50000, 90000)},
                    "Interlomas": {"lat": 19.3926, "lng": -99.2918, "price_range": (20000, 35000)},
                    "Pedregal": {"lat": 19.3223, "lng": -99.2071, "price_range": (35000, 55000)},
                    "Cuauhtémoc": {"lat": 19.4284, "lng": -99.1419, "price_range": (15000, 25000)},
                    "Juárez": {"lat": 19.4251, "lng": -99.1659, "price_range": (20000, 35000)},
                },
                "phone_prefix": "55"
            }
        }

        # Property types with realistic distributions
        self.property_types = [
            ("departamento", 45, {"min_size": 40, "max_size": 200, "bedrooms": (0, 3)}),
            ("casa", 30, {"min_size": 100, "max_size": 500, "bedrooms": (2, 5)}),
            ("terreno", 15, {"min_size": 100, "max_size": 5000, "bedrooms": (0, 0)}),
            ("oficina", 5, {"min_size": 30, "max_size": 500, "bedrooms": (0, 2)}),
            ("penthouse", 5, {"min_size": 100, "max_size": 400, "bedrooms": (2, 4)})
        ]

        # Mexican agent names
        self.agent_names = [
            "María González Rodríguez", "Carlos Hernández López", "Ana Martínez Sánchez",
            "José Luis Pérez García", "Claudia Ramírez Torres", "Miguel Ángel Flores Morales",
            "Patricia Jiménez Ruiz", "Francisco Javier Cruz Vargas", "Mónica Castillo Herrera",
            "Ricardo Moreno Mendoza", "Silvia Ortega Delgado", "Eduardo Ramos Guerrero",
            "Lucía Vázquez Romero", "Alejandro Gutiérrez Silva", "Gabriela Medina Castro",
            "Roberto Aguilar Núñez", "Carmen Salinas Rivera", "Diego Vega Campos",
            "Esperanza Contreras Morán", "Raúl Domínguez Peña", "Isabel Rojas Espinoza",
            "Sergio Campos Reyes", "Marisol Navarro Ibarra", "Arturo Soto Valdez"
        ]

        # Spanish amenities
        self.amenities_pool = [
            "alberca", "gimnasio", "jardín", "terraza", "estacionamiento", "seguridad 24h",
            "roof garden", "área de juegos", "salón de fiestas", "business center",
            "elevador", "bodega", "balcón", "vista panorámica", "cocina integral",
            "aire acondicionado", "calefacción", "chimenea", "cuarto de servicio",
            "estudio", "vestidor", "jacuzzi", "cancha de tenis", "área verde"
        ]

        # Sources with distribution
        self.sources = [
            ("inmuebles24", 40),
            ("vivanuncios", 30), 
            ("century21", 20),
            ("propiedades.com", 10)
        ]

        # CDMX neighborhood market trends (YoY growth %)
        self.market_trends = {
            "Polanco": 6,
            "Lomas de Chapultepec": 7,
            "Condesa": 9,
            "Roma Norte": 10,
            "Roma Sur": 8,
            "Santa Fe": 5,
            "Pedregal": 7,
            "San Ángel": 8,
            "Del Valle": 6,
            "Juárez": 9,
            "Nápoles": 7,
            "Coyoacán": 8,
            "Interlomas": 6,
            "Narvarte": 5,
            "Cuauhtémoc": 4
        }

    def clear_existing_data(self):
        """Clear all existing data"""
        print("🧹 Clearing existing data...")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM listings")
        cursor.execute("DELETE FROM price_history")  
        cursor.execute("DELETE FROM neighborhood_stats")
        cursor.execute("DELETE FROM duplicates")
        
        conn.commit()
        conn.close()
        print("✅ Database cleared")

    def generate_weighted_choice(self, choices):
        """Generate weighted random choice"""
        items = []
        weights = []
        for item, weight in choices:
            items.append(item)
            weights.append(weight)
        return random.choices(items, weights=weights, k=1)[0]

    def generate_listing_title(self, property_type, neighborhood, features=None):
        """Generate realistic Spanish listing titles"""
        templates = {
            "departamento": [
                f"Departamento de lujo en {neighborhood}",
                f"Hermoso departamento en {neighborhood}",
                f"Departamento moderno en {neighborhood}",
                f"Departamento con vista en {neighborhood}",
                f"Exclusivo departamento en {neighborhood}"
            ],
            "casa": [
                f"Casa moderna en {neighborhood}",
                f"Hermosa casa en {neighborhood}",
                f"Casa con jardín en {neighborhood}",
                f"Residencia en {neighborhood}",
                f"Casa familiar en {neighborhood}"
            ],
            "terreno": [
                f"Terreno en {neighborhood}",
                f"Lote en zona de plusvalía {neighborhood}",
                f"Terreno comercial en {neighborhood}",
                f"Terreno residencial en {neighborhood}",
                f"Excelente terreno en {neighborhood}"
            ],
            "oficina": [
                f"Oficina en {neighborhood}",
                f"Espacio comercial en {neighborhood}",
                f"Local comercial en {neighborhood}",
                f"Oficina ejecutiva en {neighborhood}",
                f"Oficina moderna en {neighborhood}"
            ],
            "penthouse": [
                f"Penthouse de lujo en {neighborhood}",
                f"Exclusivo penthouse en {neighborhood}",
                f"Penthouse con vista panorámica en {neighborhood}",
                f"Penthouse moderno en {neighborhood}",
                f"Espectacular penthouse en {neighborhood}"
            ]
        }
        
        titles = templates.get(property_type, templates["departamento"])
        base_title = random.choice(titles)
        
        # Add features occasionally
        if features and random.random() < 0.3:
            feature_additions = {
                "alberca": "con alberca",
                "vista panorámica": "con vista al parque", 
                "terraza": "con terraza",
                "jardín": "con jardín privado",
                "estacionamiento": "con estacionamiento"
            }
            for feature in features:
                if feature in feature_additions and random.random() < 0.5:
                    base_title += f" {feature_additions[feature]}"
                    break
        
        return base_title

    def generate_listing_description(self, property_type, city, neighborhood, amenities, size_m2):
        """Generate realistic Spanish descriptions"""
        base_descriptions = {
            "departamento": [
                f"Hermoso departamento ubicado en {neighborhood}, {city}. ",
                f"Moderno departamento en la exclusiva zona de {neighborhood}. ",
                f"Departamento de lujo en el corazón de {neighborhood}. "
            ],
            "casa": [
                f"Espectacular casa en {neighborhood}, {city}. ",
                f"Hermosa residencia ubicada en {neighborhood}. ",
                f"Casa moderna con excelentes acabados en {neighborhood}. "
            ],
            "terreno": [
                f"Excelente terreno en {neighborhood}, {city}. ",
                f"Terreno en zona de alta plusvalía en {neighborhood}. ",
                f"Lote residencial en {neighborhood} con gran potencial. "
            ],
            "oficina": [
                f"Oficina moderna en {neighborhood}, {city}. ",
                f"Espacio comercial en excelente ubicación en {neighborhood}. ",
                f"Local comercial en zona comercial de {neighborhood}. "
            ],
            "penthouse": [
                f"Exclusivo penthouse en {neighborhood}, {city}. ",
                f"Penthouse de lujo con acabados premium en {neighborhood}. ",
                f"Espectacular penthouse con vistas panorámicas en {neighborhood}. "
            ]
        }

        # Location highlights by colonia
        location_highlights = {
            "Polanco": ["cerca de Zona Rosa", "estación de metro cercana", "zona comercial premium"],
            "Condesa": ["cerca del Parque México", "vida nocturna vibrante", "zona gastronómica"],
            "Roma Norte": ["cercano a Condesa", "arquitectura colonial", "zona cultural"],
            "Roma Sur": ["cerca de Zona Rosa", "excelente conectividad", "zona residencial"],
            "Santa Fe": ["distrito financiero", "centros comerciales", "corporativos cercanos"],
            "Coyoacán": ["centro histórico", "cerca de UNAM", "zona cultural"],
            "Del Valle": ["metro cercano", "zona residencial", "centros comerciales"],
            "Narvarte": ["excelente ubicación central", "transporte público", "zona comercial"],
            "Nápoles": ["cerca de Zona Rosa", "ubicación estratégica", "fácil acceso"],
            "San Ángel": ["zona histórica", "ambiente colonial", "cerca de CU"],
            "Lomas de Chapultepec": ["zona exclusiva", "bosques cercanos", "alta plusvalía"],
            "Interlomas": ["zona empresarial", "centros comerciales", "areas verdes"],
            "Pedregal": ["arquitectura única", "zona exclusiva", "cerca de UNAM"],
            "Cuauhtémoc": ["centro de la ciudad", "excelente conectividad", "zona comercial"],
            "Juárez": ["cerca de Zona Rosa", "vida nocturna", "galerías de arte"]
        }

        base = random.choice(base_descriptions.get(property_type, base_descriptions["departamento"]))
        
        # Add size info
        base += f"Cuenta con {size_m2:.0f}m² de construcción. "
        
        # Add amenities
        if amenities:
            amenities_text = ", ".join(amenities[:3])  # First 3 amenities
            base += f"Incluye {amenities_text}. "
        
        # Add location highlight based on neighborhood
        highlights = location_highlights.get(neighborhood, ["excelente ubicación"])
        base += f"Ubicado en zona {random.choice(highlights)}."

        return base

    def generate_listing(self, target_count=400):
        """Generate realistic listings"""
        print(f"🏠 Generating {target_count} listings across CDMX...")
        
        listings_generated = 0
        
        # Calculate listings per colonia (weighted by desirability/size)
        colonia_weights = {
            "Polanco": 12,
            "Condesa": 10,
            "Roma Norte": 10,
            "Roma Sur": 8,
            "Santa Fe": 9,
            "Coyoacán": 7,
            "Del Valle": 8,
            "Narvarte": 6,
            "Nápoles": 6,
            "San Ángel": 5,
            "Lomas de Chapultepec": 7,
            "Interlomas": 5,
            "Pedregal": 4,
            "Cuauhtémoc": 2,
            "Juárez": 1
        }

        city = "Ciudad de México"
        city_data = self.cities_data[city]

        for colonia, weight in colonia_weights.items():
            colonia_target = int((weight / 100) * target_count)
            
            for i in range(colonia_target):
                try:
                    # Use the specific colonia we're iterating through
                    neighborhood = colonia
                    neighborhood_data = city_data["neighborhoods"][neighborhood]
                    
                    # Select property type based on distribution
                    property_type, _, type_config = random.choices(
                        self.property_types,
                        weights=[w for _, w, _ in self.property_types],
                        k=1
                    )[0]
                    
                    # Generate size
                    size_m2 = random.uniform(type_config["min_size"], type_config["max_size"])
                    
                    # Calculate price based on neighborhood range and property type
                    min_price_per_m2, max_price_per_m2 = neighborhood_data["price_range"]
                    price_per_m2 = random.uniform(min_price_per_m2, max_price_per_m2)
                    
                    # Apply property type multipliers
                    if property_type == "penthouse":
                        price_per_m2 *= 1.5
                    elif property_type == "casa":
                        price_per_m2 *= random.uniform(1.1, 1.3)
                    elif property_type == "terreno":
                        price_per_m2 *= random.uniform(0.8, 1.2)
                    elif property_type == "oficina":
                        price_per_m2 *= random.uniform(0.9, 1.2)
                        
                    price_mxn = price_per_m2 * size_m2
                    
                    # Generate bedrooms/bathrooms
                    if property_type == "terreno":
                        bedrooms = None
                        bathrooms = None
                        lot_size_m2 = size_m2
                    else:
                        min_bed, max_bed = type_config["bedrooms"]
                        bedrooms = random.randint(min_bed, max_bed) if max_bed > 0 else None
                        bathrooms = random.randint(1, min(4, bedrooms + 1)) if bedrooms else 1
                        lot_size_m2 = size_m2 * random.uniform(1.5, 3.0) if property_type == "casa" else None
                    
                    # Generate amenities
                    amenities_count = random.randint(2, 6)
                    amenities = random.sample(self.amenities_pool, min(amenities_count, len(self.amenities_pool)))
                    
                    # Generate coordinates with small random offset
                    lat = neighborhood_data["lat"] + random.uniform(-0.005, 0.005)
                    lng = neighborhood_data["lng"] + random.uniform(-0.005, 0.005)
                    
                    # Generate agent info
                    agent_name = random.choice(self.agent_names)
                    phone_prefix = city_data["phone_prefix"]
                    agent_phone = f"{phone_prefix}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
                    
                    # Generate source
                    source = self.generate_weighted_choice(self.sources)
                    
                    # Generate images
                    seed = f"{city}_{neighborhood}_{property_type}_{i}"
                    image_seed = hashlib.md5(seed.encode()).hexdigest()[:8]
                    images = [f"https://picsum.photos/seed/{image_seed}/800/600"]
                    
                    # Generate listing date (last 90 days)
                    days_ago = random.randint(1, 90)
                    listed_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
                    
                    # Generate title and description
                    title = self.generate_listing_title(property_type, neighborhood, amenities)
                    description = self.generate_listing_description(
                        property_type, city, neighborhood, amenities, size_m2
                    )
                    
                    listing = {
                        "source": source,
                        "source_id": f"prod-{source}-{listings_generated + 1:06d}",
                        "url": f"https://{source}.com.mx/propiedad/{listings_generated + 1:06d}",
                        "title": title,
                        "price_mxn": round(price_mxn, 2),
                        "price_usd": round(price_mxn / 17.0, 2),
                        "property_type": property_type,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "size_m2": round(size_m2, 2),
                        "lot_size_m2": round(lot_size_m2, 2) if lot_size_m2 else None,
                        "state": city_data["state"],
                        "city": city,
                        "colonia": neighborhood,
                        "lat": lat,
                        "lng": lng,
                        "description": description,
                        "images": images,
                        "agent_name": agent_name,
                        "agent_phone": agent_phone,
                        "listed_date": listed_date,
                        "amenities": amenities,
                        "parking_spaces": random.randint(0, 3) if property_type != "terreno" else None,
                    }
                    
                    listing_id = self.db.insert_listing(listing)
                    listings_generated += 1
                    
                    if listings_generated % 50 == 0:
                        print(f"✓ Generated {listings_generated} listings...")
                        
                except Exception as e:
                    print(f"✗ Error generating listing: {e}")
                    continue
        
        print(f"✅ Generated {listings_generated} total listings")
        return listings_generated

    def generate_price_history(self):
        """Generate 12 months of price history data for each colonia"""
        print("📈 Generating price history data...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        city_data = self.cities_data["Ciudad de México"]
        
        for colonia, growth_rate in self.market_trends.items():
            for month in range(12):
                # Calculate date
                date = datetime.now() - timedelta(days=30 * month)
                
                # Get base price for this colonia
                colonia_data = city_data["neighborhoods"].get(colonia)
                if not colonia_data:
                    continue
                    
                # Calculate average price for this colonia
                min_price, max_price = colonia_data["price_range"]
                base_price = (min_price + max_price) / 2
                
                # Apply reverse growth (older = lower prices)
                monthly_growth = growth_rate / 12 / 100
                price_factor = (1 + monthly_growth) ** (-month)
                historical_price = base_price * price_factor
                
                # Add some randomness
                historical_price *= random.uniform(0.95, 1.05)
                
                # Insert market trend data
                cursor.execute('''
                    INSERT INTO price_history (listing_id, price_mxn, recorded_date)
                    VALUES (?, ?, ?)
                ''', (f"market_avg_cdmx_{colonia.lower().replace(' ', '_')}", 
                     round(historical_price, 2), 
                     date.isoformat()))
        
        conn.commit()
        conn.close()
        print("✅ Price history generated")

    def generate_neighborhood_stats(self):
        """Generate neighborhood statistics"""
        print("📊 Calculating neighborhood statistics...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Clear existing stats
        cursor.execute("DELETE FROM neighborhood_stats")
        
        for city, city_data in self.cities_data.items():
            for neighborhood in city_data["neighborhoods"].keys():
                for property_type in ["departamento", "casa", "terreno", "oficina", "penthouse"]:
                    # Get stats from actual listings
                    cursor.execute('''
                        SELECT 
                            AVG(price_mxn) as avg_price,
                            AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2,
                            COUNT(*) as count,
                            MIN(price_mxn) as min_price,
                            MAX(price_mxn) as max_price,
                            AVG(size_m2) as avg_size
                        FROM listings
                        WHERE city = ? AND colonia = ? AND property_type = ?
                    ''', (city, neighborhood, property_type))
                    
                    row = cursor.fetchone()
                    
                    if row and row['count'] > 0:
                        cursor.execute('''
                            INSERT OR REPLACE INTO neighborhood_stats 
                            (city, colonia, property_type, avg_price_mxn, avg_price_per_m2, 
                             median_price_mxn, listing_count, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            city, 
                            neighborhood, 
                            property_type,
                            round(row['avg_price'], 2) if row['avg_price'] else 0,
                            round(row['avg_price_per_m2'], 2) if row['avg_price_per_m2'] else 0,
                            round(row['avg_price'], 2) if row['avg_price'] else 0,  # Using avg as median approximation
                            row['count'],
                            datetime.now().isoformat()
                        ))
        
        conn.commit()
        conn.close()
        print("✅ Neighborhood statistics generated")

    def print_final_stats(self):
        """Print final database statistics"""
        stats = self.db.get_stats()
        
        print("\n" + "=" * 60)
        print("🎉 POLPI MX PRODUCTION DATA GENERATED")
        print("=" * 60)
        print(f"📊 Total listings: {stats['total_listings']}")
        print(f"🏙️  Cities: {stats['cities']}")
        print(f"🏘️  Neighborhoods: {stats['colonias']}")
        print(f"\n📊 Listings by source:")
        for source, count in stats['sources'].items():
            print(f"   • {source}: {count} listings")
        
        # Show sample listing
        sample_listings = self.db.get_listings(limit=1)
        if sample_listings:
            sample = sample_listings[0]
            print(f"\n🏠 Sample listing:")
            print(f"   • {sample['title']}")
            print(f"   • ${sample['price_mxn']:,.2f} MXN (${sample['price_usd']:,.2f} USD)")
            print(f"   • {sample['size_m2']}m² in {sample['colonia']}, {sample['city']}")
            print(f"   • Quality score: {sample['data_quality_score']}")
        
        print(f"\n✅ Database ready at data/polpi.db")
        print(f"🚀 Run: python3 api_server.py")

def main():
    print("🐙 POLPI MX PRODUCTION DATA GENERATOR")
    print("=" * 60)
    
    generator = ProductionDataGenerator()
    
    # Clear existing data
    generator.clear_existing_data()
    
    # Generate listings
    total_generated = generator.generate_listing(target_count=400)
    
    if total_generated > 0:
        # Generate supporting data
        generator.generate_price_history()
        generator.generate_neighborhood_stats()
        
        # Show final stats
        generator.print_final_stats()
    else:
        print("❌ No listings were generated")

if __name__ == "__main__":
    main()