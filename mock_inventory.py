"""
Mock travel inventory, ported from the original agent.py.

This keeps the Gemini-powered app grounded in the same deterministic,
curated data as the eval-tested version of the project, rather than
letting the model invent flight prices or hotel names out of thin air.
Gemini's job is to hold the conversation and decide *when* to call these
tools and *how* to assemble the results into a day plan -- not to
hallucinate the underlying inventory.
"""

import random

KNOWN_DESTINATIONS: dict[str, dict] = {
    "bali":       {"country": "Indonesia", "tags": ["beach", "nature", "spiritual"]},
    "tokyo":      {"country": "Japan", "tags": ["urban", "culture", "food"]},
    "kyoto":      {"country": "Japan", "tags": ["culture", "history", "temples"]},
    "paris":      {"country": "France", "tags": ["culture", "romance", "food"]},
    "rome":       {"country": "Italy", "tags": ["history", "culture", "food"]},
    "lisbon":     {"country": "Portugal", "tags": ["coastal", "culture", "nightlife"]},
    "reykjavik":  {"country": "Iceland", "tags": ["nature", "adventure", "landscape"]},
    "queenstown": {"country": "New Zealand", "tags": ["adventure", "nature", "extreme sports"]},
    "cape town":  {"country": "South Africa", "tags": ["nature", "adventure", "coastal"]},
    "marrakech":  {"country": "Morocco", "tags": ["culture", "markets", "history"]},
    "bangkok":    {"country": "Thailand", "tags": ["food", "urban", "culture"]},
    "goa":        {"country": "India", "tags": ["beach", "relaxing", "nightlife"]},
    "manali":     {"country": "India", "tags": ["adventure", "nature", "mountains"]},
    "rishikesh":  {"country": "India", "tags": ["spiritual", "adventure", "nature"]},
    "cancun":     {"country": "Mexico", "tags": ["beach", "relaxing", "family"]},
    "banff":      {"country": "Canada", "tags": ["nature", "adventure", "mountains"]},
    "santorini":  {"country": "Greece", "tags": ["beach", "romance", "relaxing"]},
}

BUDGET_TIERS = {"budget": (0, 60), "mid": (60, 180), "luxury": (180, float("inf"))}

VIBE_PACING = {
    "relaxing":    {"activities_per_day": 2, "favored_tags": ["beach", "relaxing", "spa", "nature"]},
    "adventurous": {"activities_per_day": 4, "favored_tags": ["adventure", "extreme sports", "nature", "mountains"]},
    "cultural":    {"activities_per_day": 3, "favored_tags": ["culture", "history", "temples", "markets", "food"]},
}

_FLIGHT_CARRIERS = ["IndiGo Air", "SkyBridge", "Meridian Airlines", "Coastal Wings", "Northbound"]
_HOTEL_NAMES_BY_TIER = {
    "budget": ["{dest} Backpackers Hostel", "Traveler's Nest {dest}", "{dest} Budget Inn"],
    "mid": ["{dest} Garden Hotel", "The {dest} Collective", "Hotel {dest} Central"],
    "luxury": ["{dest} Grand Resort & Spa", "The Ritz Terrace {dest}", "{dest} Palace Hotel"],
}
_ACTIVITY_LIBRARY = {
    "beach": ["Sunset beach walk", "Snorkeling trip", "Beach clean & swim", "Catamaran sail"],
    "relaxing": ["Spa & massage session", "Rooftop lounge afternoon", "Slow breakfast + free morning", "Sunset viewpoint"],
    "spa": ["Traditional spa ritual", "Hot spring soak"],
    "nature": ["Guided nature walk", "Botanical garden visit", "Waterfall hike (easy)", "Sunrise viewpoint hike"],
    "adventure": ["White-water rafting", "Paragliding session", "Zipline canopy tour", "Rock climbing intro"],
    "extreme sports": ["Bungee jump", "Skydiving (tandem)", "Canyon swing"],
    "mountains": ["Day hike to base camp", "Cable car + summit viewpoint", "Mountain biking trail"],
    "culture": ["Old town walking tour", "Local artisan workshop", "Traditional dance show"],
    "history": ["Guided historic-site tour", "Museum of national history", "Ancient ruins visit"],
    "temples": ["Sunrise temple visit", "Temple complex walking tour"],
    "markets": ["Night market food crawl", "Local souk / bazaar tour"],
    "food": ["Street food tasting tour", "Cooking class", "Local market + lunch tasting"],
    "romance": ["Sunset river cruise", "Candlelit dinner reservation"],
    "urban": ["City skyline observation deck", "Neighborhood cafe hop"],
    "nightlife": ["Rooftop bar evening", "Live music venue night"],
    "family": ["Interactive science museum", "Wildlife park visit"],
    "spiritual": ["Meditation session with local guide", "Sunrise riverside ceremony visit"],
}


def classify_budget_tier(budget_total_usd: float, duration_days: int, travelers: int) -> str:
    per_person_per_day = budget_total_usd / max(duration_days, 1) / max(travelers, 1)
    for tier, (low, high) in BUDGET_TIERS.items():
        if low <= per_person_per_day < high:
            return tier
    return "luxury"


def search_flights_raw(destination: str, budget_tier: str, travelers: int) -> list[dict]:
    rng = random.Random(f"flights-{destination}-{budget_tier}")
    base_price = {"budget": 220, "mid": 480, "luxury": 950}[budget_tier]
    options = []
    for _ in range(3):
        price = round(base_price * rng.uniform(0.85, 1.25))
        options.append({
            "carrier": rng.choice(_FLIGHT_CARRIERS),
            "price_per_person_usd": price,
            "total_price_usd": price * travelers,
            "class": "Economy" if budget_tier != "luxury" else rng.choice(["Premium Economy", "Business"]),
            "stops": 0 if budget_tier == "luxury" else rng.choice([0, 1]),
        })
    return sorted(options, key=lambda o: o["total_price_usd"])


def search_hotels_raw(destination: str, budget_tier: str, nights: int) -> list[dict]:
    rng = random.Random(f"hotels-{destination}-{budget_tier}")
    base_nightly = {"budget": 18, "mid": 90, "luxury": 320}[budget_tier]
    names = _HOTEL_NAMES_BY_TIER[budget_tier]
    options = []
    for name_template in names:
        nightly = round(base_nightly * rng.uniform(0.85, 1.2))
        options.append({
            "name": name_template.format(dest=destination.title()),
            "tier": budget_tier,
            "nightly_rate_usd": nightly,
            "total_stay_usd": nightly * nights,
            "rating": round(rng.uniform(*{"budget": (3.4, 4.2), "mid": (4.0, 4.6), "luxury": (4.5, 5.0)}[budget_tier]), 1),
        })
    return sorted(options, key=lambda o: o["nightly_rate_usd"])


def search_activities_raw(destination: str, vibe: str, budget_tier: str) -> list[dict]:
    info = KNOWN_DESTINATIONS[destination]
    pacing = VIBE_PACING[vibe]
    rng = random.Random(f"activities-{destination}-{vibe}-{budget_tier}")
    price_band = {"budget": (0, 25), "mid": (15, 70), "luxury": (50, 250)}[budget_tier]

    candidate_tags = [t for t in pacing["favored_tags"] if t in info["tags"]] or info["tags"]
    pool = []
    for tag in candidate_tags:
        pool.extend(_ACTIVITY_LIBRARY.get(tag, []))
    for tag in info["tags"]:
        pool.extend(_ACTIVITY_LIBRARY.get(tag, []))
    pool = list(dict.fromkeys(pool))

    results = [{"name": act, "price_usd": round(rng.uniform(*price_band))} for act in pool]
    rng.shuffle(results)
    return results
