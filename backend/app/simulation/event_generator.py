"""Synthetic event generator for Simulation Mode"""
import random
from typing import Any, Dict, Tuple

EVENT_WEIGHTS = {
    "campaign_launch": 0.35,
    "budget_request": 0.25,
    "recruitment_request": 0.20,
    "resource_request": 0.20,
}

CAMPAIGN_NAMES = [
    "Spring Sale",
    "Referral Push",
    "Brand Awareness Blitz",
    "Product Launch Hype",
    "Holiday Promo",
    "Influencer Partnership",
    "Retargeting Sprint",
    "Loyalty Rewards",
]


def generate_event() -> Tuple[str, Dict[str, Any]]:
    """Pick a random event type and a randomized payload for it"""
    event_type = random.choices(
        list(EVENT_WEIGHTS.keys()), weights=list(EVENT_WEIGHTS.values()), k=1
    )[0]

    if event_type == "campaign_launch":
        return event_type, {
            "campaign_name": random.choice(CAMPAIGN_NAMES),
            "requested_budget": round(random.uniform(1000, 60000), 2),
        }
    if event_type == "budget_request":
        return event_type, {
            "department": random.choice(["Operations", "HR", "General"]),
            "amount": round(random.uniform(500, 20000), 2),
        }
    if event_type == "recruitment_request":
        return event_type, {
            "role": random.choice(["Engineer", "Sales Rep", "Designer", "Support Agent"]),
            "headcount": random.randint(1, 5),
        }
    return event_type, {
        "resource_type": random.choice(["Cloud Compute", "Office Space", "Equipment"]),
        "quantity": random.randint(1, 10),
    }
