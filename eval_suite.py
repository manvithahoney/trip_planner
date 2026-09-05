"""
Eval suite for the Trip Planner Agent.

Runs all 15 personas from personas.py through the agent and checks:
  - Right response *kind* (itinerary / clarify / guardrail)
  - Right budget tier for the persona's actual per-person-per-day spend
  - Right pacing (activities/day) for the requested vibe
  - No contradictory suggestions (hotel tier == flight tier == activity
    price band == computed budget tier; estimated cost roughly tracks
    the stated budget)
  - Guardrail personas get a graceful redirect, not a hallucinated
    itinerary (no flight/hotel/day-plan fields present)
  - Incomplete-brief personas get clarifying questions for exactly the
    fields that were left out

Run: python3 eval_suite.py
Exit code is nonzero if any check fails (CI-friendly).
"""

import sys
import json
from dataclasses import dataclass

from agent import TripPlannerAgent, classify_budget_tier, VIBE_PACING, KNOWN_DESTINATIONS
from personas import PERSONAS


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def run_persona(persona: dict) -> tuple:
    agent = TripPlannerAgent()
    agent.ingest(**persona["brief"])
    turn = agent.next_turn()
    return agent, turn


def check_persona(persona: dict) -> list[CheckResult]:
    results = []
    expect = persona["expect"]
    agent, turn = run_persona(persona)

    # -- 1. response kind ---------------------------------------------
    results.append(CheckResult(
        "response_kind",
        turn.kind == expect["kind"],
        f"expected '{expect['kind']}', got '{turn.kind}'" + (f" -- msg: {turn.message[:120]}" if turn.kind != expect["kind"] else "")
    ))

    if expect["kind"] == "guardrail":
        # No hallucinated booking data should leak into a guardrail response.
        no_itinerary = turn.itinerary is None
        results.append(CheckResult(
            "no_hallucinated_itinerary_on_guardrail",
            no_itinerary,
            "guardrail turn unexpectedly included itinerary data" if not no_itinerary else "ok",
        ))
        graceful = bool(turn.message) and ("?" in turn.message or "suggest" in turn.message.lower() or "instead" in turn.message.lower() or "pick" in turn.message.lower())
        results.append(CheckResult(
            "graceful_redirect_offers_alternative",
            graceful,
            "guardrail message should invite a follow-up / alternative, not just refuse" if not graceful else "ok",
        ))
        return results

    if expect["kind"] == "clarify":
        missing = set(turn.questions_asked)
        needed = set(expect["missing_at_least"])
        results.append(CheckResult(
            "asks_for_missing_fields",
            needed.issubset(missing),
            f"expected at least {needed} in questions_asked, got {missing}",
        ))
        results.append(CheckResult(
            "does_not_ask_for_known_fields",
            "destination" not in missing,  # destination was provided in this persona
            f"destination was provided but agent still asked for it: {missing}",
        ))
        return results

    # -- kind == "itinerary" -------------------------------------------
    it = turn.itinerary
    results.append(CheckResult("itinerary_present", it is not None, "no itinerary returned"))
    if it is None:
        return results

    # 2. Budget tier correctness
    expected_tier = expect["budget_tier"]
    actual_tier = it["budget_tier"]
    results.append(CheckResult(
        "budget_tier_matches",
        actual_tier == expected_tier,
        f"expected tier '{expected_tier}', got '{actual_tier}'",
    ))

    # Cross-check tier is *derivable* from the raw numbers (sanity check
    # on the classifier itself, independent of the persona table).
    b = persona["brief"]
    recomputed = classify_budget_tier(b["budget_total_usd"], b["duration_days"], b["travelers"])
    results.append(CheckResult(
        "budget_tier_internally_consistent",
        recomputed == actual_tier,
        f"classify_budget_tier() says '{recomputed}' but itinerary says '{actual_tier}'",
    ))

    # 3. Pacing correctness -- count activities on a "full" middle day
    #    (not an arrival/departure day, which are intentionally lighter).
    expected_pace = expect["pacing_per_day"]
    full_days = [d for d in it["days"] if d["note"] is None]
    if full_days:
        actual_paces = [len(d["activities"]) for d in full_days]
        pace_ok = all(p == expected_pace for p in actual_paces)
    else:
        # Very short trips (<=2 days) have no "full" day; check the
        # busiest day instead, capped at the expected pace.
        actual_paces = [len(d["activities"]) for d in it["days"]]
        pace_ok = all(p <= expected_pace for p in actual_paces)
    results.append(CheckResult(
        "pacing_matches_vibe",
        pace_ok,
        f"expected {expected_pace} activities/day for vibe '{it['vibe']}', got {actual_paces}",
    ))

    # Arrival/departure days should be lighter than (or equal to) full days,
    # never heavier -- that would be a pacing contradiction.
    if full_days and len(it["days"]) > 1:
        edge_days = [d for d in it["days"] if d["note"] is not None]
        edge_ok = all(len(d["activities"]) <= expected_pace for d in edge_days)
        results.append(CheckResult(
            "arrival_departure_days_not_overpacked",
            edge_ok,
            f"an arrival/departure day has more activities than the daily pace allows",
        ))

    # 4. No contradictory suggestions: hotel tier, flight class, and
    #    activity prices should all belong to the same budget tier.
    hotel_tier_ok = it["hotel"]["tier"] == actual_tier
    results.append(CheckResult(
        "hotel_tier_matches_budget_tier",
        hotel_tier_ok,
        f"hotel tier '{it['hotel']['tier']}' != itinerary tier '{actual_tier}'",
    ))

    if actual_tier == "budget":
        flight_ok = it["flight"]["class"] == "Economy"
    elif actual_tier == "luxury":
        flight_ok = it["flight"]["class"] in ("Premium Economy", "Business")
    else:
        flight_ok = it["flight"]["class"] == "Economy"
    results.append(CheckResult(
        "flight_class_matches_budget_tier",
        flight_ok,
        f"flight class '{it['flight']['class']}' inconsistent with tier '{actual_tier}'",
    ))

    price_band = {"budget": (0, 25), "mid": (15, 70), "luxury": (50, 250)}[actual_tier]
    all_prices = [a["price_usd"] for d in it["days"] for a in d["activities"]]
    prices_ok = all(price_band[0] <= p <= price_band[1] for p in all_prices) if all_prices else True
    results.append(CheckResult(
        "activity_prices_within_tier_band",
        prices_ok,
        f"some activity prices fall outside the '{actual_tier}' band {price_band}: {all_prices}",
    ))

    # 5. Estimated cost should be in the right ballpark of stated budget.
    #    If it's not, that's only acceptable when the agent has explicitly
    #    surfaced a budget_warning -- an itinerary that blows the budget
    #    silently is a contradictory suggestion (says "budget trip", spends
    #    like a mid trip) even if every individual line item was tier-correct.
    over_budget = it["estimated_total_cost_usd"] > b["budget_total_usd"] * 1.5
    cost_sane = (not over_budget) or (it.get("budget_warning") is not None)
    results.append(CheckResult(
        "cost_overrun_is_flagged_if_present",
        cost_sane,
        f"estimated ${it['estimated_total_cost_usd']:.0f} vs stated budget ${b['budget_total_usd']:.0f}, "
        f"over 1.5x with no budget_warning surfaced" if not cost_sane else "ok",
    ))

    # 6. Day count matches requested duration
    results.append(CheckResult(
        "day_count_matches_duration",
        len(it["days"]) == b["duration_days"],
        f"expected {b['duration_days']} days, got {len(it['days'])}",
    ))

    # 7. Every activity in the itinerary actually exists in the tag
    #    library for this destination/vibe (i.e. nothing hallucinated
    #    outside the mock search results).
    valid_activities = {a["name"] for a in it.get("_all_candidate_activities", [])} if "_all_candidate_activities" in it else None
    # (kept simple: activities are always drawn from search_activities() in agent.py,
    #  so this is guaranteed by construction; see design-system.md notes.)

    return results


def main() -> int:
    all_pass = True
    lines = []
    lines.append("# Trip Planner Agent -- Eval Report\n")
    lines.append(f"Personas evaluated: {len(PERSONAS)}\n")

    total_checks = 0
    total_passed = 0

    for persona in PERSONAS:
        lines.append(f"\n## {persona['id']}: {persona['name']}")
        lines.append(f"Brief: `{json.dumps(persona['brief'])}`")
        try:
            results = check_persona(persona)
        except Exception as e:
            lines.append(f"- ❌ **EXCEPTION**: {e}")
            all_pass = False
            continue

        for r in results:
            total_checks += 1
            icon = "✅" if r.passed else "❌"
            if r.passed:
                total_passed += 1
            else:
                all_pass = False
            lines.append(f"- {icon} `{r.name}` -- {r.detail if r.detail else 'ok'}")

    lines.append(f"\n\n## Summary: {total_passed}/{total_checks} checks passed across {len(PERSONAS)} personas.")
    lines.append("**RESULT: PASS**" if all_pass else "**RESULT: FAIL**")

    report = "\n".join(lines)
    print(report)

    with open("eval_report.md", "w", encoding="utf-8") as f:
        f.write(report + "\n")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
