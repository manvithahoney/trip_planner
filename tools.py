"""
Tool functions exposed to Gemini via automatic function calling.

Each function has type-hinted parameters and a docstring with an Args
section -- the google-genai SDK reads these to build the function-calling
schema automatically, so the docstrings below are not just documentation,
they're load-bearing.

Every function returns a JSON string. That keeps the contract simple and
unambiguous for the model to read back and reason about.
"""

import json

import mock_inventory as inv


def list_available_destinations() -> str:
    """Lists every destination this travel agent can actually search.

    Call this if the user names a destination you're not sure is in the
    inventory, or if they ask what places are available. Do not guess --
    check this list before telling a user their destination isn't supported.

    Returns:
        A JSON array of objects, each with "name", "country", and "tags".
    """
    out = [
        {"name": name.title(), "country": info["country"], "tags": info["tags"]}
        for name, info in inv.KNOWN_DESTINATIONS.items()
    ]
    return json.dumps(out)


def search_flights(destination: str, budget_tier: str, travelers: int) -> str:
    """Searches mock flight inventory to a destination.

    Args:
        destination: Lowercase destination name. Must be one of the names
            returned by list_available_destinations (lowercased).
        budget_tier: One of "budget", "mid", or "luxury".
        travelers: Number of travelers, as a positive integer.

    Returns:
        A JSON array of up to 3 flight options, sorted cheapest first, each
        with carrier, price_per_person_usd, total_price_usd, class, and stops.
        Returns a JSON object with an "error" key if the destination or tier
        is not recognized.
    """
    dest = destination.strip().lower()
    if dest not in inv.KNOWN_DESTINATIONS:
        return json.dumps({"error": f"'{destination}' is not in the flight inventory."})
    if budget_tier not in inv.BUDGET_TIERS:
        return json.dumps({"error": f"'{budget_tier}' is not a valid budget tier."})
    return json.dumps(inv.search_flights_raw(dest, budget_tier, max(1, travelers)))


def search_hotels(destination: str, budget_tier: str, nights: int) -> str:
    """Searches mock hotel inventory in a destination, scoped to one budget tier.

    Args:
        destination: Lowercase destination name from list_available_destinations.
        budget_tier: One of "budget", "mid", or "luxury". Only hotels in this
            exact tier are returned -- never mix tiers for the same traveler.
        nights: Number of nights of the stay, as a positive integer.

    Returns:
        A JSON array of up to 3 hotel options, sorted cheapest first, each
        with name, tier, nightly_rate_usd, total_stay_usd, and rating.
        Returns a JSON object with an "error" key if the destination or tier
        is not recognized.
    """
    dest = destination.strip().lower()
    if dest not in inv.KNOWN_DESTINATIONS:
        return json.dumps({"error": f"'{destination}' is not in the hotel inventory."})
    if budget_tier not in inv.BUDGET_TIERS:
        return json.dumps({"error": f"'{budget_tier}' is not a valid budget tier."})
    return json.dumps(inv.search_hotels_raw(dest, budget_tier, max(1, nights)))


def search_activities(destination: str, vibe: str, budget_tier: str) -> str:
    """Searches mock activities in a destination, matched to a vibe and budget tier.

    Args:
        destination: Lowercase destination name from list_available_destinations.
        vibe: One of "relaxing", "adventurous", or "cultural". This also
            determines the expected pacing: relaxing=2 activities/day,
            adventurous=4/day, cultural=3/day. Arrival and departure days
            should get one fewer activity than that pace.
        budget_tier: One of "budget", "mid", or "luxury". Only activities
            priced for this tier are returned.

    Returns:
        A JSON array of activity options, each with name and price_usd, in
        no particular order -- pick enough of them to fill each day at the
        vibe's pace without repeating an activity within the trip.
        Returns a JSON object with an "error" key if inputs are invalid.
    """
    dest = destination.strip().lower()
    if dest not in inv.KNOWN_DESTINATIONS:
        return json.dumps({"error": f"'{destination}' is not in the activity inventory."})
    if vibe not in inv.VIBE_PACING:
        return json.dumps({"error": f"'{vibe}' is not a valid vibe."})
    if budget_tier not in inv.BUDGET_TIERS:
        return json.dumps({"error": f"'{budget_tier}' is not a valid budget tier."})
    return json.dumps(inv.search_activities_raw(dest, vibe, budget_tier))


def classify_budget_tier(budget_total_usd: float, duration_days: int, travelers: int) -> str:
    """Classifies a trip's budget into a tier based on spend per person per day.

    Args:
        budget_total_usd: The traveler's total stated budget in US dollars.
        duration_days: Length of the trip in days.
        travelers: Number of travelers.

    Returns:
        A JSON object: {"tier": "budget"|"mid"|"luxury", "per_person_per_day_usd": <number>}.
        Tiers: budget < $60/person/day, mid $60-180, luxury $180+.
    """
    tier = inv.classify_budget_tier(budget_total_usd, duration_days, travelers)
    per_day = budget_total_usd / max(duration_days, 1) / max(travelers, 1)
    return json.dumps({"tier": tier, "per_person_per_day_usd": round(per_day, 2)})


ALL_TOOLS = [
    list_available_destinations,
    search_flights,
    search_hotels,
    search_activities,
    classify_budget_tier,
]
