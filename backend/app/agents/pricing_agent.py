import os
import pandas as pd


class PricingAgent:
    def __init__(self):
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(current_file)
            )
        )
        self.pricing_path = os.path.join(
            project_root,
            "app",
            "data",
            "pricing.csv"
        )
        self.pricing = pd.read_csv(self.pricing_path)

    def calculate_pricing(self, route_id, base_freight):
        pricing_data = self.pricing[
            self.pricing["route_id"] == route_id
        ]

        if pricing_data.empty:
            return {
                "status": "not_found",
                "message": f"No pricing data found for route {route_id}"
            }

        pricing = pricing_data.iloc[0]

        fuel_surcharge = float(pricing["fuel_surcharge_usd"])
        port_charge = float(pricing["port_charge_usd"])
        risk_surcharge = float(pricing["risk_surcharge_usd"])
        demand_factor = float(pricing["demand_factor"])
        target_margin = float(pricing["target_margin_percent"])

        operating_cost = (
            base_freight + fuel_surcharge + port_charge + risk_surcharge
        )
        demand_adjusted_cost = operating_cost * demand_factor

        return {
            "status": "success",
            "route_id": route_id,
            "base_freight_usd": base_freight,
            "fuel_surcharge_usd": fuel_surcharge,
            "port_charge_usd": port_charge,
            "risk_surcharge_usd": risk_surcharge,
            "demand_factor": demand_factor,
            "operating_cost_usd": round(operating_cost, 2),
            "demand_adjusted_cost_usd": round(demand_adjusted_cost, 2),
            "target_margin_percent": target_margin,
        }
