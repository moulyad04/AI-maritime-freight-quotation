"""
Customer-safe views of a quotation.

Internal business figures (operating cost, demand factor, target margin,
risk uplift, margin amount) are removed before anything is sent to a
customer. Admins still receive the full data.

The customer sees the real price broken into base freight, fuel surcharge,
port charges and one combined "service & risk handling" line. That last
line is simply what is left after the first three, so the lines always add
up exactly to the price per container - even after an admin edits the price.
"""


def _customer_pricing(pricing, final_price_per_container):
    base = float(pricing.get("base_freight_usd", 0) or 0)
    fuel = float(pricing.get("fuel_surcharge_usd", 0) or 0)
    port = float(pricing.get("port_charge_usd", 0) or 0)
    final = float(final_price_per_container)

    return {
        "base_freight_usd": round(base, 2),
        "fuel_surcharge_usd": round(fuel, 2),
        "port_charge_usd": round(port, 2),
        "service_and_risk_fee_usd": round(final - base - fuel - port, 2),
        "final_price_per_container_usd": round(final, 2),
    }


def customer_quotation(quotation):
    """For a freshly generated quotation (top-level keys)."""
    view = dict(quotation)
    pricing = view.pop("pricing", None)
    view.pop("margin", None)

    if pricing:
        view["pricing"] = _customer_pricing(
            pricing, view["freight_per_container_usd"]
        )
    return view


def customer_record(record):
    """For a stored quotation row (internal data lives under 'details')."""
    view = dict(record)
    details = view.get("details")

    if details:
        details = dict(details)
        pricing = details.pop("pricing", None)
        details.pop("margin", None)
        if pricing:
            details["pricing"] = _customer_pricing(
                pricing, view["freight_per_container_usd"]
            )
        view["details"] = details

    return view