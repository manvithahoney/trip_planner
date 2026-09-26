"""
Runtime validation for itineraries Gemini produces.

This is the same rule set eval_suite.py checks against the deterministic
mock agent, applied here as a live guardrail on the LLM's output: if
Gemini's itinerary breaks one of these rules, app.py sends it back with a
specific correction request rather than showing the person a broken plan.
"""

VIBE_PACING = {"relaxing": 2, "adventurous": 4, "cultural": 3}
PRICE_BANDS = {"budget": (0, 25), "mid": (15, 70), "luxury": (50, 250)}


def validate_itinerary(itinerary: dict) -> list[str]:
    """Returns a list of human-readable violation messages. Empty = valid."""
    problems = []

    required_top = ["destination", "vibe", "budget_tier", "flight", "hotel", "days"]
    for field in required_top:
        if field not in itinerary:
            problems.append(f"Missing required field '{field}'.")
    if problems:
        return problems  # can't check further without the basics

    vibe = itinerary.get("vibe")
    tier = itinerary.get("budget_tier")
    days = itinerary.get("days", [])

    if vibe not in VIBE_PACING:
        problems.append(f"vibe '{vibe}' is not one of relaxing/adventurous/cultural.")
    if tier not in PRICE_BANDS:
        problems.append(f"budget_tier '{tier}' is not one of budget/mid/luxury.")
    if not days:
        problems.append("days array is empty.")

    if vibe in VIBE_PACING and days:
        expected = VIBE_PACING[vibe]
        n = len(days)
        for d in days:
            day_num = d.get("day")
            count = len(d.get("activities", []))
            is_edge = day_num in (1, n) and n > 1
            allowed = max(1, expected - 1) if is_edge else expected
            if is_edge and count > allowed:
                problems.append(
                    f"Day {day_num} is an arrival/departure day with {count} activities, "
                    f"but should have at most {allowed} for vibe '{vibe}' (pace is {expected}/day)."
                )
            elif not is_edge and count != expected:
                problems.append(
                    f"Day {day_num} has {count} activities, but vibe '{vibe}' should have "
                    f"exactly {expected} on a full day."
                )

    if tier in PRICE_BANDS:
        lo, hi = PRICE_BANDS[tier]
        for d in days:
            for a in d.get("activities", []):
                price = a.get("price_usd") or a.get("price")
                if price is not None and not (lo <= price <= hi):
                    problems.append(
                        f"Activity '{a.get('name')}' costs ${price}, outside the "
                        f"${lo}-${hi} band for tier '{tier}'."
                    )

    hotel = itinerary.get("hotel", {})
    if hotel.get("tier") and tier and hotel["tier"] != tier:
        problems.append(f"Hotel tier '{hotel['tier']}' does not match itinerary tier '{tier}'.")

    return problems
