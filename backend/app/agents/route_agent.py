import os
import pandas as pd


class RouteAgent:
    def __init__(self):
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(current_file)
            )
        )
        self.dataset_path = os.path.join(
            project_root,
            "app",
            "data",
            "routes.csv"
        )
        self.routes = pd.read_csv(self.dataset_path)

    def analyze_route(self, origin, destination, cargo_type, containers):
        matching_routes = self.routes[
            (self.routes["origin"].str.lower() == origin.lower())
            & (self.routes["destination"].str.lower() == destination.lower())
        ].copy()

        if matching_routes.empty:
            return {
                "status": "not_found",
                "message": f"No route found from {origin} to {destination}"
            }

        max_transit = matching_routes["transit_days"].max()
        matching_routes["transit_score"] = (
            100 - (matching_routes["transit_days"] / max_transit * 100)
        )

        max_distance = matching_routes["distance_nm"].max()
        matching_routes["distance_score"] = (
            100 - (matching_routes["distance_nm"] / max_distance * 100)
        )

        matching_routes["transshipment_score"] = (
            100 - (matching_routes["transshipments"] * 20)
        )

        matching_routes["route_score"] = (
            matching_routes["transit_score"] * 0.40
            + matching_routes["distance_score"] * 0.25
            + matching_routes["transshipment_score"] * 0.35
        )

        matching_routes = matching_routes.sort_values(
            "route_score", ascending=False
        )

        best_route = matching_routes.iloc[0]

        alternatives = []
        for rank, (_, route) in enumerate(
            matching_routes.iloc[1:].iterrows(), start=2
        ):
            alternatives.append({
                "rank": rank,
                "route_id": route["route_id"],
                "route_type": route["route_type"],
                "transit_days": int(route["transit_days"]),
                "distance_nm": int(route["distance_nm"]),
                "transshipments": int(route["transshipments"]),
                "route_score": round(float(route["route_score"]), 2),
                "base_freight_usd": float(route["base_freight_usd"]),
                "score_breakdown": {
                    "transit_score": round(float(route["transit_score"]), 2),
                    "distance_score": round(float(route["distance_score"]), 2),
                    "transshipment_score": round(float(route["transshipment_score"]), 2),
                }
            })

        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "cargo_type": cargo_type,
            "containers": containers,
            "recommended_route": best_route["route_id"],
            "recommendation_rank": 1,
            "candidate_routes": len(matching_routes),
            "route_type": best_route["route_type"],
            "transit_time_days": int(best_route["transit_days"]),
            "distance_nm": int(best_route["distance_nm"]),
            "transshipments": int(best_route["transshipments"]),
            "route_score": round(float(best_route["route_score"]), 2),
            "score_breakdown": {
                "transit_score": round(float(best_route["transit_score"]), 2),
                "distance_score": round(float(best_route["distance_score"]), 2),
                "transshipment_score": round(float(best_route["transshipment_score"]), 2),
            },
            "base_freight_usd": float(best_route["base_freight_usd"]),
            "alternatives": alternatives,
            "reason": (
                "Route selected using weighted transit time, "
                "distance, and transshipment analysis."
            )
        }
