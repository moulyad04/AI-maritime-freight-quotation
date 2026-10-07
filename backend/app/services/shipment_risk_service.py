class ShipmentRiskService:
    """
    Shipment Risk Report: combines the weather risk and the customs risk
    into one overall risk level, with a short summary and actions to take.
    """

    LEVELS = ["LOW", "MEDIUM", "HIGH"]

    def build_report(self, weather, customs):
        weather_risk = (
            weather.get("weather_risk", "UNKNOWN")
            if weather.get("status") == "success"
            else "UNKNOWN"
        )
        customs_risk = (
            customs.get("customs_risk", "UNKNOWN")
            if customs.get("status") == "success"
            else "UNKNOWN"
        )

        known = [r for r in (weather_risk, customs_risk) if r in self.LEVELS]
        overall = max(known, key=self.LEVELS.index) if known else "UNKNOWN"

        recommendations = []
        if weather.get("status") == "success":
            recommendations.append(weather["recommendation"])
        else:
            recommendations.append(
                "No weather data available for this route; check conditions manually."
            )

        if customs.get("missing_documents"):
            recommendations.append(
                "Prepare missing customs documents before booking: "
                + ", ".join(customs["missing_documents"])
                + "."
            )
        else:
            recommendations.append("Customs documents look complete.")

        summaries = {
            "LOW": "Low overall risk. The shipment can proceed as planned.",
            "MEDIUM": "Moderate overall risk. Monitor conditions and confirm paperwork.",
            "HIGH": "High overall risk. Review the route and paperwork before committing.",
            "UNKNOWN": "Risk could not be fully assessed.",
        }

        return {
            "overall_risk": overall,
            "weather_risk": weather_risk,
            "customs_risk": customs_risk,
            "summary": summaries[overall],
            "recommendations": recommendations,
        }