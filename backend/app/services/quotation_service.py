from app.agents.route_agent import RouteAgent
from app.agents.pricing_agent import PricingAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.customs_agent import CustomsAgent
from app.agents.margin_agent import MarginAgent
from app.services.shipment_risk_service import ShipmentRiskService


class QuotationService:
    """
    Runs the full agent pipeline for one customer request:

    Route Agent -> Pricing Agent + Weather Agent -> Customs Agent
    -> Shipment Risk Report -> Margin Agent -> final quotation
    """

    def __init__(self):
        self.route_agent = RouteAgent()
        self.pricing_agent = PricingAgent()
        self.weather_agent = WeatherAgent()
        self.customs_agent = CustomsAgent()
        self.margin_agent = MarginAgent()
        self.risk_service = ShipmentRiskService()

    def generate_quotation(
        self,
        origin,
        destination,
        cargo_type,
        containers,
        documents_ready=None
    ):
        # 1. Route Agent
        route_result = self.route_agent.analyze_route(
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            containers=containers
        )

        if route_result["status"] != "success":
            return route_result

        route_id = route_result["recommended_route"]
        base_freight = route_result["base_freight_usd"]

        # 2. Pricing Agent
        pricing = self.pricing_agent.calculate_pricing(route_id, base_freight)
        if pricing["status"] != "success":
            # No pricing row: fall back to base freight with a default margin
            pricing = {
                "status": "fallback",
                "route_id": route_id,
                "base_freight_usd": base_freight,
                "fuel_surcharge_usd": 0.0,
                "port_charge_usd": 0.0,
                "risk_surcharge_usd": 0.0,
                "demand_factor": 1.0,
                "operating_cost_usd": base_freight,
                "demand_adjusted_cost_usd": base_freight,
                "target_margin_percent": 15.0,
            }

        # 3. Weather Agent
        weather = self.weather_agent.assess_weather(route_id)

        # 4. Customs Agent
        customs = self.customs_agent.validate_shipment(
            cargo_type=cargo_type,
            destination=destination,
            containers=containers,
            documents_ready=documents_ready
        )

        # 5. Shipment Risk Report
        risk_report = self.risk_service.build_report(weather, customs)

        # 6. Margin Agent
        margin = self.margin_agent.calculate_margin(
            demand_adjusted_cost=pricing["demand_adjusted_cost_usd"],
            target_margin_percent=pricing["target_margin_percent"],
            overall_risk=risk_report["overall_risk"]
        )

        price_per_container = margin["selling_price_per_container_usd"]
        total_price = round(price_per_container * containers, 2)

        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "cargo_type": cargo_type,
            "containers": containers,
            "recommended_route": route_id,
            "route_type": route_result["route_type"],
            "distance_nm": route_result["distance_nm"],
            "transshipments": route_result["transshipments"],
            "route_score": route_result["route_score"],
            "transit_time_days": route_result["transit_time_days"],
            "base_freight_usd": base_freight,
            "freight_per_container_usd": price_per_container,
            "total_freight_usd": total_price,
            "pricing": pricing,
            "weather": weather,
            "customs": customs,
            "risk_report": risk_report,
            "margin": margin,
            "alternatives": route_result["alternatives"],
            "message": "Quotation generated successfully."
        }