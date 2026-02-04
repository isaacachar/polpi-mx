#!/usr/bin/env python3
"""Add more real listings from Benito Juárez area"""

import sys
import json
import re
import hashlib
from datetime import datetime

# Add project root to path for database import
sys.path.insert(0, '/Users/isaachomefolder/Desktop/polpi-mx')
from database import PolpiDB

def extract_price_from_text(text):
    """Extract price from Mexican format text"""
    if not text:
        return None
    
    # Look for patterns like "$ 6,500,000 MXN" or "USD 2,070,000"
    if 'USD' in text:
        # Convert USD to MXN (approximate rate 20:1)
        usd_match = re.search(r'USD\s*([\d,]+)', text)
        if usd_match:
            usd_price = float(usd_match.group(1).replace(',', ''))
            return usd_price * 20  # Approximate conversion
    
    # Look for MXN prices
    mxn_match = re.search(r'\$\s*([\d,]+)\s*MXN', text)
    if mxn_match:
        return float(mxn_match.group(1).replace(',', ''))
    
    # Look for just $ amounts
    dollar_match = re.search(r'\$\s*([\d,]+)', text)
    if dollar_match:
        return float(dollar_match.group(1).replace(',', ''))
    
    return None

def get_additional_listings():
    """Get additional real listings from the Benito Juárez area snapshot"""
    additional_listings = [
        # Development projects
        {
            'title': 'Gabriel Mancera 112',
            'price_text': 'Desde $ 6,499,999 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 120,
            'colonia': 'Del Valle, Benito Juárez',
            'description': '🏙️ Gabriel Mancera 112 – Exclusividad, diseño y ubicación privilegiada Vive en el corazón de la Ciudad de México en Gabriel Mancera 112, un exclusivo desarrollo de solo 8 departamentos, 2 penthouses y 2 towhouse.',
            'url': 'https://www.lamudi.com.mx/desarrollo/41032-73-ecc04001fe91-a75e-d3228cc0-8324-4714',
            'parking_spaces': 2
        },
        {
            'title': 'MANUEL LOPEZ COTILLA 830',
            'price_text': 'Desde $ 8,925,000 MXN',
            'bedrooms': 3,
            'bathrooms': 4,
            'size_m2': 133,
            'colonia': 'Del Valle, Benito Juárez',
            'description': 'Ubicado en MANUEL LOPEZ COTILLA 830 6 casas en condominio 2 lugares de estacionamiento Bodega Estanca Comedor 3 recamaras 3 a 4 baños Sala de TV Terraza.',
            'url': 'https://www.lamudi.com.mx/desarrollo/41032-73-f516f8ca3f1a-541a-c63470d6-aa8d-4944',
            'parking_spaces': 2
        },
        # Individual listings
        {
            'title': 'Departamento en Venta en Xoco - Mitikah Tower',
            'price_text': '$ 19,990,000 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 215,
            'colonia': 'Xoco, Benito Juárez',
            'description': 'Mitikah el desarrollo Emblemático. ¡La Torre Residencial Más Alta de Latinoamérica! ¡La Mejor Orientaciòn! Vista al Sur de CDMX. Sky Residence de 3 recámaras.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-665b6b884083-5109-ba8aade1-84ad-3a92',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en Venta en Letrán Valle',
            'price_text': '$ 4,950,000 MXN',
            'bedrooms': 2,
            'bathrooms': 2,
            'size_m2': 86,
            'colonia': 'Letrán Valle, Benito Juárez',
            'description': 'Sala comedor, cocina abierta, balcón, dos baños, 2 recámaras, la recámara principal con baño y vestidor. Amenidades Alberca, Boliche, Sala de Cine, Kids Club.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-dbf239e4a82a-1a64-199e826-b24e-7c80',
            'parking_spaces': 2
        },
        {
            'title': 'Departamento nuevo en letran valle',
            'price_text': '$ 3,250,000 MXN',
            'bedrooms': 2,
            'bathrooms': 1,
            'size_m2': 65,
            'colonia': 'San Simón Ticumac, Benito Juárez',
            'description': 'Departamento nuevo en col. letran valle de 5to piso de 65 m2 de 2 recamaras con closet un baño, interior, estáncia, cocina integral, cuarto de lavado.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-148502897e54-c484-19aaa1f-b9fb-773d',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en venta en Nápoles',
            'price_text': '$ 6,500,000 MXN',
            'bedrooms': 1,
            'bathrooms': 2,
            'size_m2': 108,
            'colonia': 'Napoles, Benito Juárez',
            'description': 'Departamento muy iluminado, con balcón el cual te ofrece vistas de luz natural y ventilación. con excelente estado de conservación y buenos acabados, con amplias ventanas.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-aa4c4db4bebb-92eb-1994367-8c8b-707c',
            'parking_spaces': 2
        },
        {
            'title': 'Increíble Departamento Nuevo En Venta De Lujo',
            'price_text': '$ 20,006,250 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 275,
            'colonia': 'Del Valle, Benito Juárez',
            'description': 'Raelmente un departamento increíble!! Espacios muy amplios y bien definidos, con una gran terraza central que separa el área social de la privada. Proyecto arquitectónico de Atelier Ars.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-f290a5c05530-e09-1949b9b-9215-7d6e',
            'parking_spaces': 2
        },
        {
            'title': 'Venta de departamento en Colonia Del Valle',
            'price_text': '$ 6,900,000 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 149,
            'colonia': 'Del Valle, Benito Juárez',
            'description': 'Excelente ubicación le ofrece este hermoso departamento muy iluminado con espacios amplios y bien distribuidos, pisos de madera dec salam impecables. Una ubicación excepcional a pocas cuadras del WTC.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-34b0858867a5-af1e-196184e-bc5a-7ed4',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en venta NARVARTE PONIENTE',
            'price_text': '$ 5,600,000 MXN',
            'bedrooms': 2,
            'bathrooms': 2,
            'size_m2': 112,
            'colonia': 'Narvarte, Benito Juárez',
            'description': 'Venta de departamento ubicado en Narvarte Poniente Segundo piso, sala-comedor, cocina abierta equipada, dos habitaciones, piso de duela en las recamaras, dos baños completos.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-a6544466b1b3-c164-198f8bc-8736-73f8',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en San Simón Ticumac - Portales Norte',
            'price_text': '$ 5,937,000 MXN',
            'bedrooms': 2,
            'bathrooms': 2,
            'size_m2': 78,
            'colonia': 'San Simón Ticumac, Benito Juárez',
            'description': '📍 Ubicación: Eje Central Lázaro Cárdenas, Col. Portales Norte, Alcaldía Benito Juárez, CDMX. Distribución: 78.8 m² habitables 2 recámaras 2 baños completos Balcón privado.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-ea7ad6692b94-d674-19b4df5-b4a3-7556',
            'parking_spaces': 2
        },
        {
            'title': 'PH en venta Narvarte Poniente',
            'price_text': '$ 8,175,000 MXN',  # Corrected from the unrealistic 817M
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 109,
            'colonia': 'Narvarte, Benito Juárez',
            'description': 'Magnífico PH en Narvarte Poniente, con vistas maravillosas y un roof garden privado para disfrutar con la familia y los amigos. 109m2 habitables más roof garden 45m2.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-948d4ad7e199-db9d-19aa43b-84ab-7482',
            'parking_spaces': 2
        },
        {
            'title': 'PH de LUJO en col. DEL VALLE',
            'price_text': '$ 12,800,000 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 294,
            'colonia': 'Del Valle, Benito Juárez',
            'description': 'Excelente ubicación en GM, conecta con División del Norte, Beistegui, Diagonal San Antonio, Eje 5. PH con excelente distribución en 3 niveles. Con terraza, Rooftop y Family Room.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-b288d1ab4cb5-5794-196de9c-a606-7eb3',
            'parking_spaces': 3
        },
        {
            'title': 'Venta departamento Del Valle 3 recamaras',
            'price_text': '$ 5,800,000 MXN',
            'bedrooms': 3,
            'bathrooms': 2,
            'size_m2': 160,
            'colonia': 'Del Valle, Benito Juárez',
            'description': 'Venta departamento Col Del Valle Calle Amores Benito Juárez. Amplia sala comedor iluminada Cocina integral abierta con barra desayunadora 3 recámaras.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-80d7dbf9bde-f72c-19b7d9e-a149-79d8',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en NARVARTE con estacionamiento independiente',
            'price_text': '$ 5,680,000 MXN',
            'bedrooms': 2,
            'bathrooms': 2,
            'size_m2': 91,
            'colonia': 'Narvarte, Benito Juárez',
            'description': 'Excelente ubicación conecta Diagonal San Antonio, La Morena, Xola, Luz Saviñon, Vertiz y Gabriel Mancera. Nuevo, listo para estrenar. Solo 1 torre y con lugares de estacionamiento independiente.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-3b8f8305a2e1-5e6d-1927c10-8749-7950',
            'parking_spaces': 2
        },
        {
            'title': 'Departamento en Venta Colonia Napoles',
            'price_text': '$ 5,100,000 MXN',
            'bedrooms': 3,
            'bathrooms': 2,
            'size_m2': 120,
            'colonia': 'Napoles, Benito Juárez',
            'description': 'Departamento en Venta Colonia Napoles 120 m2 Construcción Cuarto de servicio 3 recámaras (La principal con baño, las secundarias con closet) 2 Baños completos.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-5695e24b2f97-2fc3-19191c1-a474-79e3',
            'parking_spaces': 1
        },
        {
            'title': 'Departamento en venta en Narvarte Poniente - Compacto',
            'price_text': '$ 2,690,000 MXN',
            'bedrooms': 2,
            'bathrooms': 1,
            'size_m2': 49,
            'colonia': 'Narvarte, Benito Juárez',
            'description': 'Departamento de un solo nivel, que combina perfectamente funcionalidad y calidez. Con dos cómodas recámaras, diseñado inteligentemente para ofrecer el máximo confort.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-d64831a8b656-473c-19a8492-a0bc-7b81',
            'parking_spaces': 0
        },
        {
            'title': 'Departamento en venta en Colonia Del Valle Centro - Exclusivo',
            'price_text': '$ 20,006,250 MXN',
            'bedrooms': 3,
            'bathrooms': 3,
            'size_m2': 275,
            'colonia': 'Insurgentes San Borja, Benito Juárez',
            'description': 'Solo 7 departamentos, exclusividad real distribuidos en 4 niveles, con diseño contemporáneo, sobrio y atemporal inspirada en el teatro de Padua, ejemplar de la arquitectura italiana.',
            'url': 'https://www.lamudi.com.mx/detalle/41032-73-c04a5330aeac-288f-19c2667-8bf0-76c8',
            'parking_spaces': 2
        }
    ]
    
    return additional_listings

def add_listings_to_db():
    """Add additional listings to the database"""
    db = PolpiDB()
    
    # Get additional listings
    new_listings_data = get_additional_listings()
    
    new_listings = []
    for listing_data in new_listings_data:
        listing = {
            'source': 'lamudi',
            'title': listing_data['title'],
            'price_mxn': extract_price_from_text(listing_data['price_text']),
            'bedrooms': listing_data['bedrooms'],
            'bathrooms': listing_data['bathrooms'],
            'size_m2': listing_data['size_m2'],
            'colonia': listing_data['colonia'],
            'description': listing_data['description'][:500] if listing_data['description'] else None,
            'url': listing_data['url'],
            'images': [],
            'parking_spaces': listing_data.get('parking_spaces', 0)
        }
        new_listings.append(listing)
    
    # Store new listings
    stored_count = 0
    for listing in new_listings:
        try:
            # Generate unique ID
            id_string = f"{listing['source']}_{listing.get('url', '')}{listing.get('title', '')}"
            listing_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
            
            # Convert images list to JSON string
            images_json = json.dumps(listing.get('images', []))
            
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO listings (
                    id, source, url, title, price_mxn, bedrooms, bathrooms, size_m2,
                    city, colonia, description, images, parking_spaces, scraped_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing_id,
                listing['source'],
                listing.get('url'),
                listing.get('title'),
                listing.get('price_mxn'),
                listing.get('bedrooms'),
                listing.get('bathrooms'),
                listing.get('size_m2'),
                'Ciudad de Mexico',  # city
                listing.get('colonia'),
                listing.get('description'),
                images_json,
                listing.get('parking_spaces', 0),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            stored_count += 1
            
        except Exception as e:
            print(f"Error storing listing '{listing.get('title', 'Unknown')}': {e}")
            continue
    
    return stored_count, new_listings

def get_total_listings_count():
    """Get total count of listings in database"""
    db = PolpiDB()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM listings")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def main():
    """Main function"""
    print("Adding more real listings from Benito Juárez area...")
    
    # Get current count
    initial_count = get_total_listings_count()
    print(f"Current listings in database: {initial_count}")
    
    # Add new listings
    stored, listings = add_listings_to_db()
    
    # Get final count
    final_count = get_total_listings_count()
    
    print(f"Added {stored} new listings")
    print(f"Total listings now in database: {final_count}")
    
    # Show samples
    print("\nSample new listings:")
    for i, listing in enumerate(listings[:5]):
        price_str = f"${listing.get('price_mxn'):,.0f}" if listing.get('price_mxn') else "N/A"
        print(f"  {i+1}. {listing['title'][:50]} - {price_str} - {listing.get('colonia', 'N/A')}")

if __name__ == '__main__':
    main()