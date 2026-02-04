#!/usr/bin/env python3
"""Enhanced price intelligence engine for Polpi MX"""

from database import PolpiDB
from config import config
from typing import Dict, List
import statistics
import random
from datetime import datetime, timedelta

class PriceIntelligence:
    def __init__(self):
        self.db = PolpiDB()
    
    def get_price_per_m2(self, listing: Dict) -> float:
        """Calculate price per m²"""
        if listing.get('price_mxn') and listing.get('size_m2') and listing['size_m2'] > 0:
            return round(listing['price_mxn'] / listing['size_m2'], 2)
        return None
    
    def analyze_listing(self, listing_id: str) -> Dict:
        """Comprehensive price analysis for a listing"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get the listing
        cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'error': 'Listing not found'}
        
        listing = dict(row)
        
        # Calculate price per m²
        price_per_m2 = self.get_price_per_m2(listing)
        
        # Get neighborhood stats
        neighborhood_stats = self.db.get_neighborhood_stats_enhanced(
            listing['city'],
            listing['colonia'],
            listing['property_type']
        )
        
        # Find comparables
        comparables = self.db.find_comparables(listing_id, limit=5)
        
        # Calculate deal score with breakdown
        deal_analysis = self.calculate_deal_score_detailed(listing, neighborhood_stats, comparables)
        
        # Price anomaly detection
        is_anomaly, anomaly_type = self.detect_anomaly(listing, neighborhood_stats)
        
        analysis = {
            'listing_id': listing_id,
            'price_mxn': listing['price_mxn'],
            'price_usd': listing['price_usd'],
            'size_m2': listing['size_m2'],
            'price_per_m2': price_per_m2,
            'neighborhood_stats': neighborhood_stats,
            'comparables': comparables,
            'deal_score': deal_analysis['score'],
            'deal_breakdown': deal_analysis['breakdown'],
            'is_anomaly': is_anomaly,
            'anomaly_type': anomaly_type,
            'recommendation': self.get_recommendation(deal_analysis['score'], is_anomaly, anomaly_type)
        }
        
        return analysis
    
    def calculate_deal_score_detailed(self, listing: Dict, neighborhood_stats: Dict, comparables: List[Dict]) -> Dict:
        """
        Calculate detailed deal score (0-100) with factor breakdown
        Higher score = better deal
        """
        if not listing.get('price_mxn') or not listing.get('size_m2'):
            return {
                'score': 50,
                'breakdown': {
                    'price_vs_market': 50,
                    'location_premium': 0,
                    'size_value': 0,
                    'data_quality': 25,
                    'comparable_analysis': 0
                }
            }
        
        breakdown = {
            'price_vs_market': 50,
            'location_premium': 0,
            'size_value': 0,
            'data_quality': 0,
            'comparable_analysis': 0
        }
        
        # Factor 1: Price vs neighborhood market (40 points)
        if neighborhood_stats and neighborhood_stats.get('avg_price_per_m2'):
            listing_price_per_m2 = self.get_price_per_m2(listing)
            if listing_price_per_m2:
                avg_price_per_m2 = neighborhood_stats['avg_price_per_m2']
                
                # Calculate relative position
                if listing_price_per_m2 < avg_price_per_m2:
                    discount_pct = (avg_price_per_m2 - listing_price_per_m2) / avg_price_per_m2
                    breakdown['price_vs_market'] = min(100, 50 + discount_pct * 100)
                else:
                    premium_pct = (listing_price_per_m2 - avg_price_per_m2) / avg_price_per_m2
                    breakdown['price_vs_market'] = max(0, 50 - premium_pct * 100)
        
        # Factor 2: Location premium analysis (20 points)
        if neighborhood_stats:
            # If property is in a premium percentile (top 25%), location is good
            if neighborhood_stats.get('p75_price_mxn') and listing['price_mxn']:
                if listing['price_mxn'] >= neighborhood_stats['p75_price_mxn']:
                    breakdown['location_premium'] = 15  # Premium location
                elif listing['price_mxn'] >= neighborhood_stats.get('median_price_mxn', 0):
                    breakdown['location_premium'] = 10  # Good location
                else:
                    breakdown['location_premium'] = 5   # Average location
        
        # Factor 3: Size value analysis (15 points)
        if listing.get('size_m2'):
            size = listing['size_m2']
            if size >= 150:  # Large property
                breakdown['size_value'] = 15
            elif size >= 100:  # Medium-large
                breakdown['size_value'] = 12
            elif size >= 70:   # Medium
                breakdown['size_value'] = 8
            else:  # Small
                breakdown['size_value'] = 5
        
        # Factor 4: Data quality (15 points)
        if listing.get('data_quality_score'):
            breakdown['data_quality'] = listing['data_quality_score'] * 15
        
        # Factor 5: Comparable analysis (10 points)
        if comparables:
            comparable_prices = [self.get_price_per_m2(c) for c in comparables if self.get_price_per_m2(c)]
            if comparable_prices:
                median_comp_price = statistics.median(comparable_prices)
                listing_price_per_m2 = self.get_price_per_m2(listing)
                
                if listing_price_per_m2 <= median_comp_price * 0.9:  # 10%+ cheaper
                    breakdown['comparable_analysis'] = 10
                elif listing_price_per_m2 <= median_comp_price * 0.95:  # 5%+ cheaper
                    breakdown['comparable_analysis'] = 8
                elif listing_price_per_m2 <= median_comp_price * 1.05:  # Within 5%
                    breakdown['comparable_analysis'] = 5
                else:
                    breakdown['comparable_analysis'] = 2
        
        # Calculate total score
        total_score = sum(breakdown.values())
        
        # Round breakdown values
        for key in breakdown:
            breakdown[key] = round(breakdown[key], 1)
        
        return {
            'score': max(0, min(100, round(total_score, 1))),
            'breakdown': breakdown
        }
    
    def get_investment_analysis(self, listing_id: str) -> Dict:
        """Comprehensive investment analysis"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get the listing
        cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'error': 'Listing not found'}
        
        listing = dict(row)
        
        if not listing.get('price_mxn'):
            return {'error': 'No price data available'}
        
        price = listing['price_mxn']
        city = listing.get('city', '')
        property_type = listing.get('property_type', '')
        size_m2 = listing.get('size_m2', 0)
        
        # City-specific rental yield estimates
        yield_estimates = {
            'Ciudad de México': {'casa': 0.045, 'departamento': 0.055, 'default': 0.05},
            'Guadalajara': {'casa': 0.055, 'departamento': 0.065, 'default': 0.06},
            'Monterrey': {'casa': 0.050, 'departamento': 0.060, 'default': 0.055},
            'Playa del Carmen': {'casa': 0.065, 'departamento': 0.075, 'default': 0.07},
            'Cancún': {'casa': 0.060, 'departamento': 0.070, 'default': 0.065},
            'default': {'casa': 0.050, 'departamento': 0.060, 'default': 0.055}
        }
        
        city_yields = yield_estimates.get(city, yield_estimates['default'])
        base_yield = city_yields.get(property_type.lower(), city_yields['default'])
        
        # Adjust yield based on price range (higher prices usually have lower yields)
        if price > 5000000:  # 5M+ pesos
            yield_adjustment = 0.98
        elif price > 3000000:  # 3-5M pesos
            yield_adjustment = 1.0
        elif price < 1000000:  # <1M pesos
            yield_adjustment = 1.05
        else:
            yield_adjustment = 1.02
        
        estimated_yield = base_yield * yield_adjustment
        
        # Calculate rental income
        annual_rental = price * estimated_yield
        monthly_rental = annual_rental / 12
        
        # Calculate investment metrics
        appreciation_scenarios = {
            'conservative': 0.04,  # 4% annual appreciation
            'moderate': 0.06,      # 6% annual appreciation  
            'optimistic': 0.08     # 8% annual appreciation
        }
        
        scenarios = {}
        for scenario, rate in appreciation_scenarios.items():
            scenarios[scenario] = {
                '1_year': {
                    'property_value': round(price * (1 + rate), 2),
                    'rental_income': round(annual_rental, 2),
                    'total_return': round(annual_rental + (price * rate), 2),
                    'roi_pct': round(((annual_rental + (price * rate)) / price) * 100, 2)
                },
                '3_year': {
                    'property_value': round(price * ((1 + rate) ** 3), 2),
                    'rental_income': round(annual_rental * 3, 2),
                    'total_return': round((annual_rental * 3) + (price * ((1 + rate) ** 3) - price), 2),
                    'roi_pct': round((((annual_rental * 3) + (price * ((1 + rate) ** 3) - price)) / price) * 100, 2)
                },
                '5_year': {
                    'property_value': round(price * ((1 + rate) ** 5), 2),
                    'rental_income': round(annual_rental * 5, 2),
                    'total_return': round((annual_rental * 5) + (price * ((1 + rate) ** 5) - price), 2),
                    'roi_pct': round((((annual_rental * 5) + (price * ((1 + rate) ** 5) - price)) / price) * 100, 2)
                }
            }
        
        # Calculate cap rate and cash-on-cash return
        # Assume 25% down payment for leveraged scenarios
        down_payment = price * 0.25
        loan_amount = price * 0.75
        mortgage_rate = 0.10  # 10% interest rate (typical in Mexico)
        monthly_mortgage = (loan_amount * (mortgage_rate/12)) / (1 - (1 + mortgage_rate/12) ** (-30*12))
        annual_mortgage = monthly_mortgage * 12
        
        # Net operating income (assuming 20% for expenses)
        noi = annual_rental * 0.8
        cap_rate = (noi / price) * 100
        cash_flow = noi - annual_mortgage
        cash_on_cash = (cash_flow / down_payment) * 100 if down_payment > 0 else 0
        
        return {
            'listing_id': listing_id,
            'purchase_price': price,
            'estimated_yield': round(estimated_yield * 100, 2),
            'monthly_rental': round(monthly_rental, 2),
            'annual_rental': round(annual_rental, 2),
            'cap_rate': round(cap_rate, 2),
            'leverage_analysis': {
                'down_payment': round(down_payment, 2),
                'loan_amount': round(loan_amount, 2),
                'monthly_mortgage': round(monthly_mortgage, 2),
                'annual_cash_flow': round(cash_flow, 2),
                'cash_on_cash_return': round(cash_on_cash, 2)
            },
            'appreciation_scenarios': scenarios,
            'investment_grade': self.get_investment_grade(estimated_yield, cap_rate, cash_on_cash),
            'risk_factors': self.get_risk_factors(listing, estimated_yield),
            'recommendations': self.get_investment_recommendations(estimated_yield, cap_rate, cash_on_cash)
        }
    
    def get_investment_grade(self, yield_pct: float, cap_rate: float, cash_on_cash: float) -> str:
        """Determine investment grade"""
        score = 0
        
        # Yield scoring
        if yield_pct > 0.07:
            score += 3
        elif yield_pct > 0.055:
            score += 2
        elif yield_pct > 0.04:
            score += 1
        
        # Cap rate scoring
        if cap_rate > 6:
            score += 2
        elif cap_rate > 4:
            score += 1
        
        # Cash-on-cash scoring
        if cash_on_cash > 10:
            score += 2
        elif cash_on_cash > 5:
            score += 1
        
        if score >= 6:
            return "A - Excelente"
        elif score >= 4:
            return "B - Buena"
        elif score >= 2:
            return "C - Moderada"
        else:
            return "D - Baja"
    
    def get_risk_factors(self, listing: Dict, yield_pct: float) -> List[str]:
        """Identify investment risk factors"""
        risks = []
        
        # Location risks
        if not listing.get('colonia'):
            risks.append("Ubicación no especificada claramente")
        
        # Data quality risks
        if listing.get('data_quality_score', 0) < 0.7:
            risks.append("Información incompleta de la propiedad")
        
        # Yield risks
        if yield_pct > 0.08:
            risks.append("Rendimiento muy alto - posible zona de mayor riesgo")
        elif yield_pct < 0.04:
            risks.append("Rendimiento bajo - zona premium con menor cashflow")
        
        # Size risks
        if listing.get('size_m2', 0) < 50:
            risks.append("Propiedad muy pequeña - mercado de renta limitado")
        
        # Price risks
        if listing.get('price_mxn', 0) > 10000000:
            risks.append("Precio muy alto - mercado limitado de compradores/inquilinos")
        
        return risks
    
    def get_investment_recommendations(self, yield_pct: float, cap_rate: float, cash_on_cash: float) -> List[str]:
        """Get investment recommendations"""
        recommendations = []
        
        if cash_on_cash > 10:
            recommendations.append("Excelente oportunidad de flujo de efectivo positivo")
        elif cash_on_cash > 0:
            recommendations.append("Flujo de efectivo positivo con apalancamiento")
        else:
            recommendations.append("Considerar mayor enganche o renegociar precio")
        
        if cap_rate > 6:
            recommendations.append("Alto retorno sobre la inversión - verificar zona")
        elif cap_rate < 3:
            recommendations.append("Zona premium - enfoque en apreciación a largo plazo")
        
        if yield_pct > 0.065:
            recommendations.append("Alto potencial de renta - investigar demanda local")
        
        return recommendations
    
    def compare_neighborhoods(self, colonias: List[str], city: str = None) -> Dict:
        """Compare multiple neighborhoods side by side"""
        if len(colonias) < 2 or len(colonias) > 3:
            return {'error': 'Debe comparar entre 2 y 3 colonias'}
        
        comparison = {
            'neighborhoods': [],
            'summary': {}
        }
        
        for colonia in colonias:
            # Try to find the city if not provided
            if not city:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT city, COUNT(*) as count
                    FROM listings 
                    WHERE colonia = ? 
                    GROUP BY city
                    ORDER BY count DESC 
                    LIMIT 1
                """, (colonia,))
                result = cursor.fetchone()
                conn.close()
                if result:
                    city = result['city']
                else:
                    continue
            
            stats = self.db.get_neighborhood_stats_enhanced(city, colonia)
            if stats:
                # Get property type breakdown
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        property_type,
                        COUNT(*) as count,
                        AVG(price_mxn) as avg_price,
                        AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
                    FROM listings
                    WHERE city = ? AND colonia = ?
                    GROUP BY property_type
                """, (city, colonia))
                property_types = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                stats['property_types'] = property_types
                comparison['neighborhoods'].append(stats)
        
        if len(comparison['neighborhoods']) >= 2:
            # Generate comparison summary
            neighborhoods = comparison['neighborhoods']
            
            # Price comparison
            prices = [n['avg_price_mxn'] for n in neighborhoods]
            comparison['summary']['most_expensive'] = neighborhoods[prices.index(max(prices))]['colonia']
            comparison['summary']['most_affordable'] = neighborhoods[prices.index(min(prices))]['colonia']
            
            # Listing volume comparison
            counts = [n['listing_count'] for n in neighborhoods]
            comparison['summary']['most_inventory'] = neighborhoods[counts.index(max(counts))]['colonia']
            comparison['summary']['least_inventory'] = neighborhoods[counts.index(min(counts))]['colonia']
            
            # Price per m² comparison
            price_per_m2 = [n['avg_price_per_m2'] for n in neighborhoods if n['avg_price_per_m2']]
            if price_per_m2:
                comparison['summary']['price_difference_pct'] = round(
                    ((max(price_per_m2) - min(price_per_m2)) / min(price_per_m2)) * 100, 1
                )
        
        return comparison
    
    def generate_price_trends(self, city: str, property_type: str = None) -> List[Dict]:
        """Get historical price trends for a city"""
        return self.db.get_market_trends(city, property_type, months=12)
    
    def detect_anomaly(self, listing: Dict, neighborhood_stats: Dict) -> tuple:
        """
        Detect if listing price is anomalous
        Returns (is_anomaly: bool, anomaly_type: str)
        """
        if not neighborhood_stats or not neighborhood_stats.get('avg_price_per_m2'):
            return (False, None)
        
        listing_price_per_m2 = self.get_price_per_m2(listing)
        if not listing_price_per_m2:
            return (False, None)
        
        avg_price_per_m2 = neighborhood_stats['avg_price_per_m2']
        
        # Calculate deviation using percentiles
        p25 = neighborhood_stats.get('p25_price_mxn')
        p75 = neighborhood_stats.get('p75_price_mxn')
        
        if p25 and p75:
            price = listing['price_mxn']
            if price < p25 * 0.7:  # Well below 25th percentile
                return (True, 'potential_steal')
            elif price > p75 * 1.3:  # Well above 75th percentile
                return (True, 'overpriced')
        
        # Fallback to simple deviation
        deviation = abs(listing_price_per_m2 - avg_price_per_m2) / avg_price_per_m2
        
        if deviation > 0.5:  # 50% deviation
            if listing_price_per_m2 > avg_price_per_m2:
                return (True, 'overpriced')
            else:
                return (True, 'potential_deal')
        
        return (False, None)
    
    def get_recommendation(self, deal_score: float, is_anomaly: bool, anomaly_type: str) -> str:
        """Get human-readable recommendation"""
        if is_anomaly and anomaly_type == 'potential_steal':
            return "🎯 ¡Oportunidad excepcional! Precio muy por debajo del mercado."
        elif is_anomaly and anomaly_type == 'potential_deal':
            return "💰 ¡Excelente oportunidad! Este precio está significativamente por debajo del promedio."
        elif is_anomaly and anomaly_type == 'overpriced':
            return "⚠️ Precio elevado. Esta propiedad está significativamente por encima del mercado."
        elif deal_score >= 80:
            return "⭐ Excelente inversión - precio muy competitivo vs mercado."
        elif deal_score >= 65:
            return "👍 Buen precio comparado con el mercado local."
        elif deal_score >= 45:
            return "📊 Precio dentro del rango de mercado."
        else:
            return "🔍 Precio por encima del promedio. Considera negociar o evaluar otros factores."
    
    def get_city_overview(self, city: str) -> Dict:
        """Enhanced city overview with market insights"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Overall city stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_listings,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2,
                MIN(price_mxn) as min_price,
                MAX(price_mxn) as max_price,
                AVG(size_m2) as avg_size
            FROM listings
            WHERE city = ? AND is_active = 1
        """, (city,))
        
        city_stats = dict(cursor.fetchone())
        
        # Top colonias by different metrics
        cursor.execute("""
            SELECT 
                colonia,
                COUNT(*) as listing_count,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
            FROM listings
            WHERE city = ? AND colonia IS NOT NULL AND size_m2 > 0 AND is_active = 1
            GROUP BY colonia
            HAVING COUNT(*) >= 3
            ORDER BY avg_price_per_m2 DESC
            LIMIT 10
        """, (city,))
        
        premium_colonias = [dict(row) for row in cursor.fetchall()]
        
        # Most affordable colonias
        cursor.execute("""
            SELECT 
                colonia,
                COUNT(*) as listing_count,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
            FROM listings
            WHERE city = ? AND colonia IS NOT NULL AND size_m2 > 0 AND is_active = 1
            GROUP BY colonia
            HAVING COUNT(*) >= 3
            ORDER BY avg_price_per_m2 ASC
            LIMIT 5
        """, (city,))
        
        affordable_colonias = [dict(row) for row in cursor.fetchall()]
        
        # Property type distribution
        cursor.execute("""
            SELECT 
                property_type,
                COUNT(*) as count,
                AVG(price_mxn) as avg_price,
                AVG(price_mxn / NULLIF(size_m2, 0)) as avg_price_per_m2
            FROM listings
            WHERE city = ? AND is_active = 1
            GROUP BY property_type
            ORDER BY count DESC
        """, (city,))
        
        property_types = [dict(row) for row in cursor.fetchall()]
        
        # Market trends
        trends = self.db.get_market_trends(city, months=6)
        
        conn.close()
        
        return {
            'city': city,
            'total_listings': city_stats['total_listings'],
            'avg_price': round(city_stats['avg_price'], 2) if city_stats['avg_price'] else 0,
            'avg_price_per_m2': round(city_stats['avg_price_per_m2'], 2) if city_stats['avg_price_per_m2'] else 0,
            'avg_size_m2': round(city_stats['avg_size'], 1) if city_stats['avg_size'] else 0,
            'price_range': {
                'min': city_stats['min_price'],
                'max': city_stats['max_price']
            },
            'premium_colonias': premium_colonias,
            'affordable_colonias': affordable_colonias,
            'property_types': property_types,
            'market_trends': trends
        }
    
    def get_trending_listings(self, city: str = None, limit: int = 10) -> List[Dict]:
        """Get listings with best deal scores"""
        filters = {}
        if city:
            filters['city'] = city
        
        listings = self.db.get_listings(filters=filters, limit=100)
        
        # Score each listing
        scored_listings = []
        for listing in listings:
            if listing.get('price_mxn') and listing.get('size_m2'):
                neighborhood_stats = self.db.get_neighborhood_stats_enhanced(
                    listing['city'],
                    listing['colonia'],
                    listing['property_type']
                )
                comparables = self.db.find_comparables(listing['id'], limit=3)
                deal_analysis = self.calculate_deal_score_detailed(listing, neighborhood_stats, comparables)
                
                listing['deal_score'] = deal_analysis['score']
                listing['price_per_m2'] = self.get_price_per_m2(listing)
                scored_listings.append(listing)
        
        # Sort by deal score
        scored_listings.sort(key=lambda x: x.get('deal_score', 0), reverse=True)
        
        return scored_listings[:limit]