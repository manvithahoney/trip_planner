# Trip Planner Agent -- Eval Report

Personas evaluated: 15


## P01: Solo backpacker, low budget
Brief: `{"destination": "bangkok", "duration_days": 6, "budget_total_usd": 250, "travelers": 1, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'budget', got 'budget'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'budget' but itinerary says 'budget'
- ✅ `pacing_matches_vibe` -- expected 4 activities/day for vibe 'adventurous', got [4, 4, 4, 4]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'budget' != itinerary tier 'budget'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Economy' inconsistent with tier 'budget'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'budget' band (0, 25): [2, 14, 18, 21, 0, 12, 15, 4, 2, 14, 18, 21, 0, 12, 15, 4, 2, 14, 18, 21, 0, 12]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 6 days, got 6

## P02: Family of 4, relaxing beach trip
Brief: `{"destination": "cancun", "duration_days": 7, "budget_total_usd": 8000, "travelers": 4, "vibe": "relaxing"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 2 activities/day for vibe 'relaxing', got [2, 2, 2, 2, 2]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Business' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [210, 84, 202, 66, 58, 213, 213, 54, 90, 50, 210, 84]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 7 days, got 7

## P03: Honeymoon couple, luxury romance
Brief: `{"destination": "santorini", "duration_days": 5, "budget_total_usd": 12000, "travelers": 2, "vibe": "relaxing"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 2 activities/day for vibe 'relaxing', got [2, 2, 2]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Business' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [229, 61, 180, 246, 136, 162, 139, 59]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 5 days, got 5

## P04: Adventure junkie, mid budget, mountains
Brief: `{"destination": "queenstown", "duration_days": 4, "budget_total_usd": 2800, "travelers": 1, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 4 activities/day for vibe 'adventurous', got [4, 4]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Premium Economy' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [215, 172, 83, 68, 147, 163, 178, 152, 232, 82, 68, 215, 172, 83]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 4 days, got 4

## P05: History buff, cultural, mid budget
Brief: `{"destination": "rome", "duration_days": 5, "budget_total_usd": 3500, "travelers": 1, "vibe": "cultural"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 3 activities/day for vibe 'cultural', got [3, 3, 3]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Business' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [161, 191, 143, 149, 141, 169, 95, 144, 191, 161, 191, 143, 149]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 5 days, got 5

## P06: Retired couple, slow cultural trip
Brief: `{"destination": "kyoto", "duration_days": 8, "budget_total_usd": 6000, "travelers": 2, "vibe": "cultural"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 3 activities/day for vibe 'cultural', got [3, 3, 3, 3, 3, 3]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Business' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [106, 77, 195, 69, 155, 189, 118, 54, 106, 77, 195, 69, 155, 189, 118, 54, 106, 77, 195, 69, 155, 189]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 8 days, got 8

## P07: College friend group, budget adventure
Brief: `{"destination": "manali", "duration_days": 5, "budget_total_usd": 1000, "travelers": 4, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'budget', got 'budget'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'budget' but itinerary says 'budget'
- ✅ `pacing_matches_vibe` -- expected 4 activities/day for vibe 'adventurous', got [4, 4, 4]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'budget' != itinerary tier 'budget'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Economy' inconsistent with tier 'budget'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'budget' band (0, 25): [21, 10, 15, 1, 8, 3, 24, 25, 8, 5, 21, 21, 10, 15, 1, 8, 3, 24]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 5 days, got 5

## P08: Digital nomad, relaxing, extended stay
Brief: `{"destination": "bali", "duration_days": 14, "budget_total_usd": 2100, "travelers": 1, "vibe": "relaxing"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'mid', got 'mid'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'mid' but itinerary says 'mid'
- ✅ `pacing_matches_vibe` -- expected 2 activities/day for vibe 'relaxing', got [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'mid' != itinerary tier 'mid'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Economy' inconsistent with tier 'mid'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'mid' band (15, 70): [21, 38, 33, 65, 58, 36, 20, 51, 38, 17, 21, 38, 33, 65, 58, 36, 20, 51, 38, 17, 21, 38, 33, 65, 58, 36]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 14 days, got 14

## P09: Spiritual seeker, mid budget
Brief: `{"destination": "rishikesh", "duration_days": 6, "budget_total_usd": 1500, "travelers": 1, "vibe": "relaxing"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 2 activities/day for vibe 'relaxing', got [2, 2, 2, 2]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Business' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [238, 73, 154, 241, 233, 148, 98, 233, 199, 140]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 6 days, got 6

## P10: Business-trip-turned-vacation, luxury, short
Brief: `{"destination": "paris", "duration_days": 3, "budget_total_usd": 6000, "travelers": 1, "vibe": "cultural"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'luxury', got 'luxury'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'luxury' but itinerary says 'luxury'
- ✅ `pacing_matches_vibe` -- expected 3 activities/day for vibe 'cultural', got [3]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'luxury' != itinerary tier 'luxury'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Premium Economy' inconsistent with tier 'luxury'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'luxury' band (50, 250): [121, 183, 141, 189, 54, 82, 186]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 3 days, got 3

## P11: Gap-year traveler, ultra low budget, long trip
Brief: `{"destination": "goa", "duration_days": 10, "budget_total_usd": 400, "travelers": 1, "vibe": "relaxing"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'budget', got 'budget'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'budget' but itinerary says 'budget'
- ✅ `pacing_matches_vibe` -- expected 2 activities/day for vibe 'relaxing', got [2, 2, 2, 2, 2, 2, 2, 2]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'budget' != itinerary tier 'budget'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Economy' inconsistent with tier 'budget'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'budget' band (0, 25): [13, 3, 19, 7, 18, 5, 12, 11, 7, 13, 13, 3, 19, 7, 18, 5, 12, 11]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 10 days, got 10

## P12: Impossible destination -- the Moon
Brief: `{"destination": "the moon", "duration_days": 5, "budget_total_usd": 5000, "travelers": 1, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'guardrail', got 'guardrail'
- ✅ `no_hallucinated_itinerary_on_guardrail` -- ok
- ✅ `graceful_redirect_offers_alternative` -- ok

## P13: Fictional destination -- Narnia
Brief: `{"destination": "narnia", "duration_days": 7, "budget_total_usd": 3000, "travelers": 2, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'guardrail', got 'guardrail'
- ✅ `no_hallucinated_itinerary_on_guardrail` -- ok
- ✅ `graceful_redirect_offers_alternative` -- ok

## P14: Incomplete brief -- missing budget and vibe
Brief: `{"destination": "lisbon", "duration_days": 5, "travelers": 2}`
- ✅ `response_kind` -- expected 'clarify', got 'clarify'
- ✅ `asks_for_missing_fields` -- expected at least {'budget', 'vibe'} in questions_asked, got {'budget', 'vibe'}
- ✅ `does_not_ask_for_known_fields` -- destination was provided but agent still asked for it: {'budget', 'vibe'}

## P15: Extreme mismatch -- luxury vibe words, near-zero budget
Brief: `{"destination": "cape town", "duration_days": 6, "budget_total_usd": 350, "travelers": 1, "vibe": "adventurous"}`
- ✅ `response_kind` -- expected 'itinerary', got 'itinerary'
- ✅ `itinerary_present` -- no itinerary returned
- ✅ `budget_tier_matches` -- expected tier 'budget', got 'budget'
- ✅ `budget_tier_internally_consistent` -- classify_budget_tier() says 'budget' but itinerary says 'budget'
- ✅ `pacing_matches_vibe` -- expected 4 activities/day for vibe 'adventurous', got [4, 4, 4, 4]
- ✅ `arrival_departure_days_not_overpacked` -- an arrival/departure day has more activities than the daily pace allows
- ✅ `hotel_tier_matches_budget_tier` -- hotel tier 'budget' != itinerary tier 'budget'
- ✅ `flight_class_matches_budget_tier` -- flight class 'Economy' inconsistent with tier 'budget'
- ✅ `activity_prices_within_tier_band` -- some activity prices fall outside the 'budget' band (0, 25): [2, 9, 23, 14, 12, 12, 20, 7, 2, 9, 23, 14, 12, 12, 20, 7, 2, 9, 23, 14, 12, 12]
- ✅ `cost_overrun_is_flagged_if_present` -- ok
- ✅ `day_count_matches_duration` -- expected 6 days, got 6


## Summary: 141/141 checks passed across 15 personas.
**RESULT: PASS**
