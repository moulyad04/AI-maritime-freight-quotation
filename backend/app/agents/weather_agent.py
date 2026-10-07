import os
import pandas as pd


class WeatherAgent:
    def __init__(self):
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(current_file)
            )
        )

        self.weather_path = os.path.join(
            project_root,
            "app",
            "data",
            "weather.csv"
        )

        self.weather = pd.read_csv(self.weather_path)

    def calculate_risk(
        self,
        wind_speed,
        wave_height,
        visibility,
        storm_probability
    ):
        risk_points = 0

        # Wind risk
        if wind_speed >= 35:
            risk_points += 3
        elif wind_speed >= 25:
            risk_points += 2
        else:
            risk_points += 1

        # Wave risk
        if wave_height >= 4.5:
            risk_points += 3
        elif wave_height >= 3:
            risk_points += 2
        else:
            risk_points += 1

        # Visibility risk
        if visibility < 8:
            risk_points += 3
        elif visibility < 12:
            risk_points += 2
        else:
            risk_points += 1

        # Storm probability risk
        if storm_probability >= 40:
            risk_points += 3
        elif storm_probability >= 20:
            risk_points += 2
        else:
            risk_points += 1

        if risk_points >= 10:
            risk_level = "HIGH"
        elif risk_points >= 7:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return risk_level, risk_points

    def assess_weather(self, route_id):
        weather_data = self.weather[
            self.weather["route_id"] == route_id
        ]

        if weather_data.empty:
            return {
                "status": "not_found",
                "message": f"No weather data found for route {route_id}"
            }

        weather = weather_data.iloc[0]

        wind_speed = float(weather["wind_speed_knots"])
        wave_height = float(weather["wave_height_m"])
        visibility = float(weather["visibility_km"])
        storm_probability = float(weather["storm_probability"])

        risk_level, risk_points = self.calculate_risk(
            wind_speed=wind_speed,
            wave_height=wave_height,
            visibility=visibility,
            storm_probability=storm_probability
        )

        if risk_level == "LOW":
            recommendation = "Proceed normally."
        elif risk_level == "MEDIUM":
            recommendation = "Monitor weather conditions."
        else:
            recommendation = (
                "Consider route review and additional risk precautions."
            )

        return {
            "status": "success",
            "route_id": route_id,
            "region": weather["region"],
            "wind_speed_knots": wind_speed,
            "wave_height_m": wave_height,
            "visibility_km": visibility,
            "storm_probability_percent": storm_probability,
            "weather_condition": weather["weather_condition"],
            "weather_risk": risk_level,
            "risk_points": risk_points,
            "recommendation": recommendation
        }