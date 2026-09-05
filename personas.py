"""
15 eval personas for the Trip Planner Agent.

Each persona is a dict of the brief fields the agent would eventually
collect through clarifying questions, plus a set of expectations the
eval suite checks against the resulting itinerary (or guardrail message).
"""

PERSONAS = [
    {
        "id": "P01",
        "name": "Solo backpacker, low budget",
        "brief": {
            "destination": "bangkok",
            "duration_days": 6,
            "budget_total_usd": 250,
            "travelers": 1,
            "vibe": "adventurous",
        },
        "expect": {"kind": "itinerary", "budget_tier": "budget", "pacing_per_day": 4},
    },
    {
        "id": "P02",
        "name": "Family of 4, relaxing beach trip",
        "brief": {
            "destination": "cancun",
            "duration_days": 7,
            "budget_total_usd": 8000,
            "travelers": 4,
            "vibe": "relaxing",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 2},
    },
    {
        "id": "P03",
        "name": "Honeymoon couple, luxury romance",
        "brief": {
            "destination": "santorini",
            "duration_days": 5,
            "budget_total_usd": 12000,
            "travelers": 2,
            "vibe": "relaxing",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 2},
    },
    {
        "id": "P04",
        "name": "Adventure junkie, mid budget, mountains",
        "brief": {
            "destination": "queenstown",
            "duration_days": 4,
            "budget_total_usd": 2800,
            "travelers": 1,
            "vibe": "adventurous",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 4},
    },
    {
        "id": "P05",
        "name": "History buff, cultural, mid budget",
        "brief": {
            "destination": "rome",
            "duration_days": 5,
            "budget_total_usd": 3500,
            "travelers": 1,
            "vibe": "cultural",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 3},
    },
    {
        "id": "P06",
        "name": "Retired couple, slow cultural trip",
        "brief": {
            "destination": "kyoto",
            "duration_days": 8,
            "budget_total_usd": 6000,
            "travelers": 2,
            "vibe": "cultural",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 3},
    },
    {
        "id": "P07",
        "name": "College friend group, budget adventure",
        "brief": {
            "destination": "manali",
            "duration_days": 5,
            "budget_total_usd": 1000,
            "travelers": 4,
            "vibe": "adventurous",
        },
        "expect": {"kind": "itinerary", "budget_tier": "budget", "pacing_per_day": 4},
    },
    {
        "id": "P08",
        "name": "Digital nomad, relaxing, extended stay",
        "brief": {
            "destination": "bali",
            "duration_days": 14,
            "budget_total_usd": 2100,
            "travelers": 1,
            "vibe": "relaxing",
        },
        "expect": {"kind": "itinerary", "budget_tier": "mid", "pacing_per_day": 2},
    },
    {
        "id": "P09",
        "name": "Spiritual seeker, mid budget",
        "brief": {
            "destination": "rishikesh",
            "duration_days": 6,
            "budget_total_usd": 1500,
            "travelers": 1,
            "vibe": "relaxing",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 2},
    },
    {
        "id": "P10",
        "name": "Business-trip-turned-vacation, luxury, short",
        "brief": {
            "destination": "paris",
            "duration_days": 3,
            "budget_total_usd": 6000,
            "travelers": 1,
            "vibe": "cultural",
        },
        "expect": {"kind": "itinerary", "budget_tier": "luxury", "pacing_per_day": 3},
    },
    {
        "id": "P11",
        "name": "Gap-year traveler, ultra low budget, long trip",
        "brief": {
            "destination": "goa",
            "duration_days": 10,
            "budget_total_usd": 400,
            "travelers": 1,
            "vibe": "relaxing",
        },
        "expect": {"kind": "itinerary", "budget_tier": "budget", "pacing_per_day": 2},
    },
    {
        "id": "P12",
        "name": "Impossible destination -- the Moon",
        "brief": {
            "destination": "the moon",
            "duration_days": 5,
            "budget_total_usd": 5000,
            "travelers": 1,
            "vibe": "adventurous",
        },
        "expect": {"kind": "guardrail"},
    },
    {
        "id": "P13",
        "name": "Fictional destination -- Narnia",
        "brief": {
            "destination": "narnia",
            "duration_days": 7,
            "budget_total_usd": 3000,
            "travelers": 2,
            "vibe": "adventurous",
        },
        "expect": {"kind": "guardrail"},
    },
    {
        "id": "P14",
        "name": "Incomplete brief -- missing budget and vibe",
        "brief": {
            "destination": "lisbon",
            "duration_days": 5,
            # budget_total_usd intentionally omitted
            "travelers": 2,
            # vibe intentionally omitted
        },
        "expect": {"kind": "clarify", "missing_at_least": ["budget", "vibe"]},
    },
    {
        "id": "P15",
        "name": "Extreme mismatch -- luxury vibe words, near-zero budget",
        "brief": {
            "destination": "cape town",
            "duration_days": 6,
            "budget_total_usd": 350,  # ~$58/person/day -- budget tier, and just barely feasible
            "travelers": 1,
            "vibe": "adventurous",
        },
        "expect": {"kind": "itinerary", "budget_tier": "budget", "pacing_per_day": 4},
    },
]
