"""
Generates routes.csv, pricing.csv and weather.csv (250 rows each) in app/data/.

Run once from the backend folder:
    python generate_datasets.py

The first 10 rows of each file are the original hand-written rows from the
milestone document. The remaining 240 rows are generated deterministically
(fixed random seed), so everyone who runs this gets identical files.
The generated values are illustrative sample data, not real market data.
"""
import csv
import os
import random

random.seed(2026)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------- originals
ORIGINAL_ROUTES = [
    ("R001", "Chennai", "Rotterdam", 8650, 24, 1, "Standard", 1850),
    ("R002", "Chennai", "Rotterdam", 9100, 27, 2, "Alternative", 1720),
    ("R003", "Chennai", "Rotterdam", 8950, 26, 1, "Alternative", 1780),
    ("R004", "Chennai", "Hamburg", 8800, 25, 1, "Standard", 1900),
    ("R005", "Mumbai", "Hamburg", 7940, 22, 1, "Standard", 1800),
    ("R006", "Mumbai", "Hamburg", 8350, 25, 2, "Alternative", 1680),
    ("R007", "Mumbai", "Rotterdam", 7600, 21, 1, "Standard", 1750),
    ("R008", "Mumbai", "Rotterdam", 8050, 24, 2, "Alternative", 1640),
    ("R009", "Singapore", "Rotterdam", 8400, 23, 1, "Standard", 1600),
    ("R010", "Singapore", "Hamburg", 8600, 24, 1, "Standard", 1650),
]

ORIGINAL_PRICING = [
    ("P001", "R001", 100, 75, 1.00, 50, 15),
    ("P002", "R002", 110, 80, 0.95, 60, 15),
    ("P003", "R003", 105, 70, 1.05, 55, 15),
    ("P004", "R004", 100, 80, 1.00, 50, 15),
    ("P005", "R005", 95, 70, 1.00, 45, 15),
    ("P006", "R006", 105, 75, 0.95, 55, 15),
    ("P007", "R007", 90, 65, 1.05, 45, 15),
    ("P008", "R008", 100, 70, 0.95, 50, 15),
    ("P009", "R009", 85, 60, 1.10, 40, 15),
    ("P010", "R010", 90, 65, 1.05, 45, 15),
]

ORIGINAL_WEATHER = [
    ("W001", "R001", "Indian Ocean", 28, 3.5, 12, 25, "Moderate"),
    ("W002", "R002", "Indian Ocean", 35, 4.8, 9, 40, "Stormy"),
    ("W003", "R003", "Indian Ocean", 30, 3.8, 10, 30, "Moderate"),
    ("W004", "R004", "North Sea", 32, 4.2, 8, 35, "Stormy"),
    ("W005", "R005", "Arabian Sea", 22, 2.5, 15, 15, "Good"),
    ("W006", "R006", "Arabian Sea", 29, 3.6, 11, 25, "Moderate"),
    ("W007", "R007", "Indian Ocean", 20, 2.0, 16, 10, "Good"),
    ("W008", "R008", "Indian Ocean", 27, 3.2, 13, 20, "Moderate"),
    ("W009", "R009", "Indian Ocean", 18, 1.8, 18, 8, "Good"),
    ("W010", "R010", "North Sea", 30, 4.0, 10, 30, "Moderate"),
]

# ------------------------------------------------------------------- ports
ORIGINS = [
    "Chennai", "Mumbai", "Kolkata", "Visakhapatnam", "Kochi",
    "Nhava Sheva", "Mundra", "Colombo", "Singapore", "Port Klang",
]

# destination -> (approx. base distance in nautical miles, weather region)
DESTINATIONS = {
    "Rotterdam": (8500, "North Sea"),
    "Hamburg": (8750, "North Sea"),
    "Antwerp": (8450, "North Sea"),
    "Felixstowe": (8400, "North Sea"),
    "Genoa": (6200, "Mediterranean Sea"),
    "Piraeus": (5400, "Mediterranean Sea"),
    "New York": (12100, "Atlantic Ocean"),
    "Los Angeles": (11400, "Pacific Ocean"),
    "Jebel Ali": (1900, "Arabian Sea"),
    "Shanghai": (3900, "South China Sea"),
    "Tokyo": (4900, "Pacific Ocean"),
    "Sydney": (5800, "Indian Ocean"),
}

# how much closer/farther each origin is compared with the base distance
ORIGIN_OFFSET = {
    "Chennai": 0, "Mumbai": -700, "Kolkata": 350, "Visakhapatnam": 150,
    "Kochi": -550, "Nhava Sheva": -720, "Mundra": -900, "Colombo": -300,
    "Singapore": -350, "Port Klang": -250,
}

# route type -> (speed nm/day, freight factor, transshipment choices)
ROUTE_TYPES = {
    "Express": (400, 1.12, [0, 1]),
    "Standard": (360, 1.00, [1]),
    "Alternative": (345, 0.94, [1, 2]),
    "Economy": (330, 0.88, [2, 3]),
}

REGION_RATE = {
    "New York": 0.235, "Los Angeles": 0.235, "Sydney": 0.225,
    "Jebel Ali": 0.30, "Shanghai": 0.26, "Tokyo": 0.25,
}
DEFAULT_RATE = 0.2139


def build_routes(target=250):
    rows = list(ORIGINAL_ROUTES)
    lanes = [(o, d) for o in ORIGINS for d in DESTINATIONS]
    random.shuffle(lanes)

    # two routes for every lane: one fast/standard, one cheaper alternative
    pair_types = [("Express", "Standard"), ("Standard", "Alternative"),
                  ("Standard", "Economy"), ("Express", "Alternative")]
    n = len(rows)
    for origin, dest in lanes:
        base = DESTINATIONS[dest][0] + ORIGIN_OFFSET[origin]
        base = max(base, 900)
        for rtype in random.choice(pair_types):
            if n >= target:
                break
            speed, factor, ts_choices = ROUTE_TYPES[rtype]
            distance = int(base * random.uniform(0.97, 1.05))
            transshipments = random.choice(ts_choices)
            days = max(2, round(distance / speed + 0.5 * transshipments))
            rate = REGION_RATE.get(dest, DEFAULT_RATE)
            freight = int(round(distance * rate * factor / 10.0) * 10)
            n += 1
            rows.append((f"R{n:03d}", origin, dest, distance, days,
                         transshipments, rtype, freight))
    return rows[:target]


def build_pricing(routes):
    rows = list(ORIGINAL_PRICING)
    freight_by_route = {r[0]: r[7] for r in routes}
    for i, route in enumerate(routes[len(rows):], start=len(rows) + 1):
        freight = freight_by_route[route[0]]
        fuel = int(round(freight * random.uniform(0.045, 0.065) / 5.0) * 5)
        port = random.choice(range(55, 100, 5))
        demand = random.choice([0.90, 0.95, 1.00, 1.05, 1.10, 1.15])
        risk = random.choice(range(35, 75, 5))
        margin = random.choice([12, 13, 14, 15, 16, 17, 18])
        rows.append((f"P{i:03d}", route[0], fuel, port, demand, risk, margin))
    return rows


def risk_level(wind, wave, vis, storm):
    """Same scoring rules as WeatherAgent.calculate_risk()."""
    pts = 0
    pts += 3 if wind >= 35 else 2 if wind >= 25 else 1
    pts += 3 if wave >= 4.5 else 2 if wave >= 3 else 1
    pts += 3 if vis < 8 else 2 if vis < 12 else 1
    pts += 3 if storm >= 40 else 2 if storm >= 20 else 1
    return "HIGH" if pts >= 10 else "MEDIUM" if pts >= 7 else "LOW"


CONDITION = {"LOW": "Good", "MEDIUM": "Moderate", "HIGH": "Stormy"}

# how rough each region tends to be: (wind range, wave range, visibility range, storm range)
REGION_PROFILE = {
    "North Sea": ((22, 40), (2.5, 5.2), (6, 16), (15, 55)),
    "Atlantic Ocean": ((24, 42), (3.0, 5.5), (6, 15), (20, 58)),
    "Pacific Ocean": ((20, 38), (2.5, 5.0), (7, 17), (15, 50)),
    "Mediterranean Sea": ((14, 32), (1.5, 3.8), (10, 20), (5, 35)),
    "Arabian Sea": ((16, 34), (1.8, 4.0), (9, 19), (8, 40)),
    "South China Sea": ((18, 38), (2.0, 4.6), (7, 18), (10, 48)),
    "Indian Ocean": ((15, 36), (1.8, 4.6), (8, 19), (8, 45)),
}


def build_weather(routes):
    rows = list(ORIGINAL_WEATHER)
    for i, route in enumerate(routes[len(rows):], start=len(rows) + 1):
        region = DESTINATIONS[route[2]][1]
        w, h, v, s = REGION_PROFILE[region]
        wind = random.randint(*w)
        wave = round(random.uniform(*h), 1)
        vis = random.randint(*v)
        storm = random.randint(*s)
        cond = CONDITION[risk_level(wind, wave, vis, storm)]
        rows.append((f"W{i:03d}", route[0], region, wind, wave, vis, storm, cond))
    return rows


def write_csv(name, header, rows):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {path}")


if __name__ == "__main__":
    routes = build_routes(250)
    pricing = build_pricing(routes)
    weather = build_weather(routes)

    write_csv(
        "routes.csv",
        ["route_id", "origin", "destination", "distance_nm", "transit_days",
         "transshipments", "route_type", "base_freight_usd"],
        routes,
    )
    write_csv(
        "pricing.csv",
        ["pricing_id", "route_id", "fuel_surcharge_usd", "port_charge_usd",
         "demand_factor", "risk_surcharge_usd", "target_margin_percent"],
        pricing,
    )
    write_csv(
        "weather.csv",
        ["weather_id", "route_id", "region", "wind_speed_knots", "wave_height_m",
         "visibility_km", "storm_probability", "weather_condition"],
        weather,
    )