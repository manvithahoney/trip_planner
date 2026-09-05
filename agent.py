"""
Trip Planner Agent
==================

A small, deterministic "agent" that:
  1. Asks clarifying questions until it has enough slots filled
     (destination, dates/duration, budget, vibe, travelers).
  2. Validates the destination against a guardrail before doing anything
     else -- unreachable / fictional places get a graceful redirect
     instead of a hallucinated itinerary.
  3. Calls mock "tool" functions for flights, hotels, and activities.
  4. Assembles a structured, day-by-day itinerary whose budget tier and
     pacing are derived from the user's answers.

The agent is intentionally rule-based rather than LLM-backed. That keeps
the tool-calling contract explicit and the whole thing eval-able:
same input -> same output, every time, which is what the eval suite in
eval_suite.py depends on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Guardrails: destination knowledge base
# ---------------------------------------------------------------------------

# A small "known world" of destinations the mock search tools can actually
# serve. In a real system this would be a geocoding / travel-inventory API
# call. Here it doubles as the guardrail: anything not resolvable is not
# real, off-limits, or off-Earth, and the agent should say so rather than
# invent flights and hotels for it.
KNOWN_DESTINATIONS: dict[str, dict] = {
    "bali":       {"country": "Indonesia", "region": "Southeast Asia", "tags": ["beach", "nature", "spiritual"]},
    "tokyo":      {"country": "Japan", "region": "East Asia", "tags": ["urban", "culture", "food"]},
    "kyoto":      {"country": "Japan", "region": "East Asia", "tags": ["culture", "history", "temples"]},
    "paris":      {"country": "France", "region": "Europe", "tags": ["culture", "romance", "food"]},
    "rome":       {"country": "Italy", "region": "Europe", "tags": ["history", "culture", "food"]},
    "lisbon":     {"country": "Portugal", "region": "Europe", "tags": ["coastal", "culture", "nightlife"]},
    "reykjavik":  {"country": "Iceland", "region": "Europe", "tags": ["nature", "adventure", "landscape"]},
    "queenstown": {"country": "New Zealand", "region": "Oceania", "tags": ["adventure", "nature", "extreme sports"]},
    "cape town":  {"country": "South Africa", "region": "Africa", "tags": ["nature", "adventure", "coastal"]},
    "marrakech":  {"country": "Morocco", "region": "Africa", "tags": ["culture", "markets", "history"]},
    "bangkok":    {"country": "Thailand", "region": "Southeast Asia", "tags": ["food", "urban", "culture"]},
    "goa":        {"country": "India", "region": "South Asia", "tags": ["beach", "relaxing", "nightlife"]},
    "manali":     {"country": "India", "region": "South Asia", "tags": ["adventure", "nature", "mountains"]},
    "rishikesh":  {"country": "India", "region": "South Asia", "tags": ["spiritual", "adventure", "nature"]},
    "cancun":     {"country": "Mexico", "region": "North America", "tags": ["beach", "relaxing", "family"]},
    "banff":      {"country": "Canada", "region": "North America", "tags": ["nature", "adventure", "mountains"]},
    "santorini":  {"country": "Greece", "region": "Europe", "tags": ["beach", "romance", "relaxing"]},
}

# Places people genuinely ask for that the mock inventory cannot serve,
# grouped so the redirect message can be a little more specific/helpful.
UNSERVICEABLE = {
    "moon": "off-planet", "mars": "off-planet", "the moon": "off-planet", "outer space": "off-planet",
    "narnia": "fictional", "atlantis": "fictional", "hogwarts": "fictional", "middle earth": "fictional",
    "westeros": "fictional", "gotham": "fictional", "wakanda": "fictional",
    "north korea": "restricted", "north sentinel island": "restricted",
}


@dataclass
class TripBrief:
    """Slots the agent needs filled before it can build an itinerary."""
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    budget_total_usd: Optional[float] = None
    travelers: int = 1
    vibe: Optional[str] = None  # "relaxing" | "adventurous" | "cultural"

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.destination:
            missing.append("destination")
        if not self.duration_days:
            missing.append("dates")
        if not self.budget_total_usd:
            missing.append("budget")
        if not self.vibe:
            missing.append("vibe")
        return missing


@dataclass
class AgentTurn:
    """What the agent produces on a single turn of the conversation."""
    kind: str  # "clarify" | "guardrail" | "itinerary"
    message: str
    itinerary: Optional[dict] = None
    questions_asked: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Budget tiers & pacing rules
# ---------------------------------------------------------------------------

BUDGET_TIERS = {
    # per-person, per-day USD thresholds
    "budget": (0, 60),
    "mid": (60, 180),
    "luxury": (180, float("inf")),
}

VIBE_PACING = {
    # activities scheduled per day, and the pool of activity "tags" favored
    "relaxing":    {"activities_per_day": 2, "favored_tags": ["beach", "relaxing", "spa", "nature"]},
    "adventurous": {"activities_per_day": 4, "favored_tags": ["adventure", "extreme sports", "nature", "mountains"]},
    "cultural":    {"activities_per_day": 3, "favored_tags": ["culture", "history", "temples", "markets", "food"]},
}


def classify_budget_tier(budget_total_usd: float, duration_days: int, travelers: int) -> str:
    per_person_per_day = budget_total_usd / max(duration_days, 1) / max(travelers, 1)
    for tier, (low, high) in BUDGET_TIERS.items():
        if low <= per_person_per_day < high:
            return tier
    return "luxury"


# ---------------------------------------------------------------------------
# Mock "search" tools
# ---------------------------------------------------------------------------
# Each mirrors what a real flight/hotel/activity search API would return,
# but is deterministic (seeded) so eval runs are reproducible.

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


def search_flights(destination: str, budget_tier: str, travelers: int) -> list[dict]:
    """Mock flight search. Returns a short list of options."""
    rng = random.Random(f"flights-{destination}-{budget_tier}")
    base_price = {"budget": 220, "mid": 480, "luxury": 950}[budget_tier]
    options = []
    for i in range(3):
        price = round(base_price * rng.uniform(0.85, 1.25))
        options.append({
            "carrier": rng.choice(_FLIGHT_CARRIERS),
            "price_per_person_usd": price,
            "total_price_usd": price * travelers,
            "class": "Economy" if budget_tier != "luxury" else rng.choice(["Premium Economy", "Business"]),
            "stops": 0 if budget_tier == "luxury" else rng.choice([0, 1]),
        })
    return sorted(options, key=lambda o: o["total_price_usd"])


def search_hotels(destination: str, budget_tier: str, nights: int) -> list[dict]:
    """Mock hotel search, scoped to the requested budget tier only --
    this is what prevents the itinerary from mixing a hostel-tier budget
    with a five-star stay (a contradictory-suggestion failure mode)."""
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
            "rating": {"budget": round(rng.uniform(3.4, 4.2), 1),
                       "mid": round(rng.uniform(4.0, 4.6), 1),
                       "luxury": round(rng.uniform(4.5, 5.0), 1)}[budget_tier],
        })
    return sorted(options, key=lambda o: o["nightly_rate_usd"])


def search_activities(destination: str, vibe: str, budget_tier: str) -> list[dict]:
    """Mock activity search filtered by vibe (pacing/tag) and budget tier
    (price band), so a 'low budget' persona never gets a $400 heli-tour."""
    info = KNOWN_DESTINATIONS[destination]
    pacing = VIBE_PACING[vibe]
    rng = random.Random(f"activities-{destination}-{vibe}-{budget_tier}")

    price_band = {"budget": (0, 25), "mid": (15, 70), "luxury": (50, 250)}[budget_tier]

    candidate_tags = [t for t in pacing["favored_tags"] if t in info["tags"]] or info["tags"]
    pool = []
    for tag in candidate_tags:
        pool.extend(_ACTIVITY_LIBRARY.get(tag, []))
    # also sprinkle in destination's own tags for variety even if not the primary favored ones
    for tag in info["tags"]:
        pool.extend(_ACTIVITY_LIBRARY.get(tag, []))
    pool = list(dict.fromkeys(pool))  # de-dup, keep order

    results = []
    for act in pool:
        price = round(rng.uniform(*price_band))
        results.append({"name": act, "price_usd": price, "tag_source": destination})
    rng.shuffle(results)
    return results


# ---------------------------------------------------------------------------
# The Agent
# ---------------------------------------------------------------------------

class TripPlannerAgent:
    """Drives a short multi-turn conversation to fill a TripBrief, then
    calls the mock tools and assembles the itinerary."""

    CLARIFYING_QUESTIONS = {
        "destination": "Where would you like to go?",
        "dates": "How many days is the trip, or what dates are you thinking?",
        "budget": "What's your total budget for the trip (in USD), roughly?",
        "vibe": "What's the vibe you're after: relaxing, adventurous, or cultural?",
    }

    def __init__(self):
        self.brief = TripBrief()

    # -- slot filling ------------------------------------------------------

    def ingest(self, **kwargs) -> None:
        """Apply any known answers onto the brief (case-insensitive dest/vibe)."""
        if "destination" in kwargs and kwargs["destination"]:
            self.brief.destination = str(kwargs["destination"]).strip().lower()
        if "duration_days" in kwargs and kwargs["duration_days"]:
            self.brief.duration_days = int(kwargs["duration_days"])
        if "budget_total_usd" in kwargs and kwargs["budget_total_usd"]:
            self.brief.budget_total_usd = float(kwargs["budget_total_usd"])
        if "travelers" in kwargs and kwargs["travelers"]:
            self.brief.travelers = int(kwargs["travelers"])
        if "vibe" in kwargs and kwargs["vibe"]:
            self.brief.vibe = str(kwargs["vibe"]).strip().lower()

    def next_turn(self) -> AgentTurn:
        """Call this after each ingest(). Returns either another clarifying
        question, a guardrail redirect, or the final itinerary."""

        # Guardrail check happens as soon as we have a destination --
        # no point asking about budget/vibe for a trip we can't serve.
        if self.brief.destination:
            guardrail_msg = self._check_guardrail(self.brief.destination)
            if guardrail_msg:
                return AgentTurn(kind="guardrail", message=guardrail_msg)

        missing = self.brief.missing_fields()
        if missing:
            questions = [self.CLARIFYING_QUESTIONS[f] for f in missing]
            return AgentTurn(
                kind="clarify",
                message=" ".join(questions),
                questions_asked=missing,
            )

        itinerary = self.build_itinerary()
        return AgentTurn(kind="itinerary", message="Here's your itinerary.", itinerary=itinerary)

    # -- guardrail -----------------------------------------------------

    @staticmethod
    def _check_guardrail(destination: str) -> Optional[str]:
        dest = destination.strip().lower()
        if dest in KNOWN_DESTINATIONS:
            return None
        if dest in UNSERVICEABLE:
            reason = UNSERVICEABLE[dest]
            if reason == "off-planet":
                return (
                    f"I can't book travel to {destination.title()} -- there's no commercial travel "
                    f"inventory for off-Earth destinations. If you meant a space-themed trip on Earth "
                    f"(e.g. a space center visit, an observatory trip, or Iceland's aurora-viewing tours), "
                    f"I'd be glad to plan that instead. Want me to suggest one?"
                )
            if reason == "fictional":
                return (
                    f"{destination.title()} isn't a real place I can find flights or hotels for. "
                    f"If you're after that kind of atmosphere, I can suggest real destinations with a similar "
                    f"feel -- just tell me what drew you to it (scenery, history, adventure) and I'll match it."
                )
            if reason == "restricted":
                return (
                    f"I'm not able to plan travel to {destination.title()} -- it's not currently serviceable "
                    f"through standard travel booking channels. Want to pick a different destination?"
                )
        # Unknown but plausibly real place: be honest about the limits of
        # the mock inventory rather than inventing flights/hotels for it.
        return (
            f"I don't have search inventory for '{destination.title()}' in this demo. "
            f"I can currently plan trips to: {', '.join(d.title() for d in sorted(KNOWN_DESTINATIONS))}. "
            f"Want to pick one of these, or a nearby alternative?"
        )

    # -- itinerary building --------------------------------------------

    def build_itinerary(self) -> dict:
        b = self.brief
        tier = classify_budget_tier(b.budget_total_usd, b.duration_days, b.travelers)
        pacing = VIBE_PACING[b.vibe]

        flights = search_flights(b.destination, tier, b.travelers)
        hotels = search_hotels(b.destination, tier, nights=b.duration_days - 1 if b.duration_days > 1 else 1)
        activities = search_activities(b.destination, b.vibe, tier)

        chosen_flight = flights[0]
        chosen_hotel = hotels[0]

        # Build day-by-day plan
        days = []
        activity_cursor = 0
        n_per_day = pacing["activities_per_day"]
        for day_num in range(1, b.duration_days + 1):
            day_plan = {"day": day_num, "activities": []}
            if day_num == 1:
                day_plan["note"] = "Arrival day -- lighter schedule to allow for travel/check-in."
                slots_today = max(1, n_per_day - 1)
            elif day_num == b.duration_days and b.duration_days > 1:
                day_plan["note"] = "Departure day -- lighter schedule to allow time for checkout/travel."
                slots_today = max(1, n_per_day - 1)
            else:
                day_plan["note"] = None
                slots_today = n_per_day

            for _ in range(slots_today):
                if activity_cursor >= len(activities):
                    activity_cursor = 0  # wrap if we run out (short trip vs long trip)
                if not activities:
                    break
                day_plan["activities"].append(activities[activity_cursor])
                activity_cursor += 1
            days.append(day_plan)

        total_activities_cost = sum(a["price_usd"] for d in days for a in d["activities"])
        est_total_cost = chosen_flight["total_price_usd"] + chosen_hotel["total_stay_usd"] + total_activities_cost

        # Budget-feasibility guardrail: flights + a room for every night are
        # non-negotiable fixed costs. If those alone already eat up most of
        # the stated budget, silently returning a "budget tier" itinerary
        # that's actually unaffordable is its own kind of nonsense-input
        # failure. Flag it explicitly instead of hiding it in the totals.
        fixed_cost = chosen_flight["total_price_usd"] + chosen_hotel["total_stay_usd"]
        budget_warning = None
        if fixed_cost > b.budget_total_usd:
            budget_warning = (
                f"Heads up: flights + the cheapest available stay alone come to about "
                f"${fixed_cost:,.0f}, which already exceeds your ${b.budget_total_usd:,.0f} budget. "
                f"Consider a longer time to save, a shorter trip, or a closer / cheaper destination."
            )
        elif est_total_cost > b.budget_total_usd * 1.5:
            budget_warning = (
                f"Heads up: the estimated total (${est_total_cost:,.0f}) is well above your stated "
                f"budget (${b.budget_total_usd:,.0f}) even at the cheapest options for this tier. "
                f"You may want to trim activity days or raise the budget."
            )

        itinerary = {
            "destination": b.destination.title(),
            "country": KNOWN_DESTINATIONS[b.destination]["country"],
            "duration_days": b.duration_days,
            "travelers": b.travelers,
            "vibe": b.vibe,
            "budget_tier": tier,
            "budget_total_usd": b.budget_total_usd,
            "flight": chosen_flight,
            "hotel": chosen_hotel,
            "days": days,
            "estimated_total_cost_usd": est_total_cost,
            "within_budget": est_total_cost <= b.budget_total_usd * 1.1,  # 10% slack
            "budget_warning": budget_warning,
        }
        return itinerary


# ---------------------------------------------------------------------------
# Convenience: run a full brief end-to-end in one call (used by evals)
# ---------------------------------------------------------------------------

def run_full_conversation(**brief_kwargs) -> AgentTurn:
    """Feed a complete brief at once (as if all clarifying questions had
    already been answered) and return the final AgentTurn."""
    agent = TripPlannerAgent()
    agent.ingest(**brief_kwargs)
    return agent.next_turn()
