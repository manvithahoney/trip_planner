# Trip Planner — Design System Notes

Documenting the design language used in `dashboard.html`, so future screens (a
booking confirmation, a multi-trip list, a "compare itineraries" view) stay
consistent instead of each one reinventing tokens.

## Concept

The dashboard is styled like a **physical travel document** — the boarding
pass and the ticket stub — rather than a generic SaaS dashboard. That
metaphor was chosen because it's the actual content: a system telling you
"here is your trip, here is day 3 of it," which is exactly what a boarding
pass or a paper itinerary from a travel agent does. The day tabs are built
as ticket stubs (a punch-hole marker, a torn-off active state) instead of
generic pill tabs, because in this domain "which stub is torn off" *is* "which
day you're looking at."

Two deliberate departures from the current AI-generated-design defaults:
warm cream + terracotta, near-black + neon accent, and hairline-broadsheet
layouts were all avoided. Instead: ink-navy + parchment + brass, which reads
as "travel document" rather than "SaaS product," and a monospace display
face used specifically to evoke a departure board.

## Color

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#14213D` | Header background, primary text on parchment |
| `--navy-deep` | `#0D1729` | Boarding-pass header panel |
| `--parchment` | `#FAF6EC` | Main content background, active tab/panel |
| `--parchment-dim` | `#F0EADA` | Inactive tab background, cost-strip background |
| `--brass` | `#C89B3C` | Tier badge, active-tab indicator, skip-link |
| `--brass-text` | `#E8C878` | Small caps labels on navy (better contrast than `--brass` at small sizes) |
| `--teal` | `#3B6E71` | Activity prices, secondary accents |
| `--rust` | `#A8402F` | Budget-warning border/icon (paired with a light rust background, not used as body text on navy) |
| `--ink` | `#24211A` | Body text on parchment |
| `--ink-soft` | `#55503F` | Secondary/meta text |
| `--line` | `#D8CFB5` | Hairline borders on parchment |
| `--focus-ring` | `#1F6FEB` | Keyboard focus outline — kept independent of the brand palette so it's never mistaken for a hover/selection color |

Contrast was checked at the pairs that carry text: navy-deep background with
parchment text, parchment background with ink text, and brass badge with
navy-deep text all clear WCAG AA for their point sizes.

## Type

| Role | Face | Where |
|---|---|---|
| Display / data | `JetBrains Mono` | Page title, day numbers, prices, eyebrow labels, tier badge — the "departure board" register |
| Body | `IBM Plex Sans` | Activity names, descriptions, running copy |

Mono is used **sparingly and consistently** — only for things that are
literally ticket/board-like (numbers, codes, labels) — not for paragraphs.
That's the rule going forward: if it's a piece of data (a price, a day
number, a status), it's mono; if it's a sentence a person reads, it's Plex
Sans.

## Layout

- Single-column, max-width `860px`, centered — itineraries are read
  top-to-bottom, not scanned in a grid.
- Boarding-pass header → cost-summary strip → day-tab strip → active day
  panel → footer. Each section has a visually distinct background
  (`navy-deep` → `parchment-dim` → `parchment`) so the eye tracks progress
  down the "document" without needing extra dividers.
- Day tabs scroll horizontally on narrow viewports rather than wrapping —
  a wrapped multi-row tab strip breaks the "single ticket strip" metaphor
  and also breaks the Left/Right arrow-key mental model (see below).

## Signature element

The **ticket-stub day tabs**: each tab carries a small punch-hole dot and
the selected tab visibly "lifts" above its neighbors with a brass underline,
echoing a torn ticket stub. This is the one place the design takes a visual
risk; everything else (cards, spacing, type scale) stays quiet so that
element reads as intentional rather than decorative.

## Accessibility patterns (binding, not optional)

These are implemented in `dashboard.html` and should carry forward to any
new screen in this system:

1. **Day tabs follow the WAI-ARIA APG Tabs Pattern exactly**:
   `role="tablist"` with an `aria-label`; each tab is `role="tab"` with
   `aria-selected` and `aria-controls`; each panel is `role="tabpanel"`
   with `aria-labelledby` and `tabindex="0"`. Roving tabindex — only the
   selected tab is reachable by <kbd>Tab</kbd>; <kbd>←</kbd>/<kbd>→</kbd>
   move between tabs (wrapping at the ends), <kbd>Home</kbd>/<kbd>End</kbd>
   jump to the first/last day. This was verified against the pattern
   spec at https://www.w3.org/WAI/ARIA/apg/patterns/tabs/ line by line
   (see `handleTabKeydown` / `activateTab` in the script) — every tab is a
   real `<button>`, not a styled `<div>`, so it's focusable and
   activatable by keyboard and assistive tech with no extra ARIA needed
   for that part.
2. **Skip link** to the day panels, visible on focus, first element in the
   DOM.
3. **`aria-live="polite"` region** for the budget-feasibility warning
   (`role="alert"` on the message itself), so if a user changes inputs
   and a warning appears, screen reader users hear it without having to
   go looking for it.
4. **Focus is never removed or hidden** — `:focus-visible` outlines use a
   dedicated `--focus-ring` color independent of the brand palette, at
   3px with a 2px offset, on every interactive element including the tabs.
5. **`prefers-reduced-motion` respected** — the only motion in the page
   (the tab "lift" transition) is gated behind a `no-preference` media
   query.
6. **Color is never the only signal** — the active tab also gets a
   position change (lift) and a border, not just a color swap; the
   budget warning has an icon-equivalent (`<strong>Budget notice —</strong>`)
   ahead of the message text, not just a red border.
7. **No positive `tabindex` values anywhere** — natural DOM order plus
   roving `tabindex="-1"/"0"` on tabs is the only tab-order manipulation
   in the page.

### How this was tested

Verified with a static structural check (semantic roles, labelling,
tabindex hygiene, reduced-motion and focus-visible coverage — see the
assertions run against the markup during the build). For a shipped version,
the next step before release should be a manual pass with a real screen
reader (VoiceOver or NVDA) navigating the tablist by arrow keys end-to-end,
plus an automated pass with axe-core in CI — neither of those was available
in this environment, and should not be assumed done based on the structural
checks alone.

## Open questions for the next screen

- If a "compare two itineraries" view gets built, does the boarding-pass
  metaphor still hold side-by-side, or does it need a lighter variant?
- The tier badge currently only has three states (budget/mid/luxury) styled
  identically in brass — worth deciding whether tiers should be visually
  distinct (e.g. budget in teal, luxury in brass) once there's a screen
  where a user compares tiers directly.

## Addendum: interactive version (v2)

`dashboard.html` was upgraded from a static, single-trip demo to a fully
interactive planner: a trip-setup form (destination, days, budget,
travelers, vibe) drives the whole agent pipeline client-side, and the
person can choose between the 3 flight options and 3 hotel options the
mock search returns — previously the agent silently picked the cheapest.
The agent logic itself (`agent.py`'s guardrails, `classify_budget_tier`,
`search_*`, and day-pacing rules) was ported to plain JavaScript so the
page needs no server or build step; a Node-based test harness mirroring
`eval_suite.py`'s checks (guardrails, tier classification, tier-consistent
flight/hotel/activity pricing, vibe pacing) was run against the ported
logic before shipping — see the project history for the 28 checks that
were verified.

New components and their accessibility treatment:

- **Trip-setup form** — native `<input>`/`<fieldset>` elements throughout;
  every field has a real `<label for>`. The vibe picker is a
  `<fieldset><legend>` group of radios styled as pill buttons (not custom
  `<div>` buttons), so screen readers announce it as a standard
  radio-group with its group name.
- **Radio-card picker** (flight/hotel choice) — same principle: real
  `<input type="radio">` elements inside `<label>` wrappers, grouped in a
  `<fieldset>` with a (visually hidden but screen-reader-visible) `<legend>`
  naming the group. The "selected" look comes from `:has(input:checked)`,
  a CSS state hook, not a JS-only visual — so the checked state and the
  visual state can never drift out of sync.
- **Guardrail message region** — switched from `aria-live="polite"` (used
  for the budget warning, which is informational) to
  `aria-live="assertive"` for the guardrail message, since it's a direct
  response to a form submission the person needs to hear about
  immediately, and focus is moved to it programmatically
  (`region.focus()`) so keyboard/screen-reader users land exactly there
  instead of having to hunt for what happened.
- **Live cost recalculation** — picking a different flight or hotel option
  re-renders the cost strip and (if relevant) the budget-warning region
  immediately, without touching the day-tabs' focus or selected state.

## Addendum 2: chat mode (v3)

The original written spec asked for an agent that "asks the user a few
clarifying questions" — the form (v2) collects the same fields but all at
once, which is good UX but doesn't demonstrate that incremental
back-and-forth. `dashboard.html` now offers a second mode, toggled via a
`<fieldset>` radio group at the top ("Quick form" / "Chat with the agent"),
that reproduces `agent.py`'s `ingest()` → `next_turn()` loop directly:

- A small `ChatAgent` class in JS holds the same brief shape
  (`destination`, `durationDays`, `budgetTotalUsd`, `travelers`, `vibe`)
  and the same `missingFields()` / guardrail-first-then-clarify-then-build
  control flow as the Python agent.
- Free-text messages are parsed with lightweight pattern matching (dollar
  amounts → budget, "N days" / "a week" / "N weeks" → duration, "solo" /
  "family of N" / "for two" → travelers, vibe keywords, and known/
  unserviceable destination names found anywhere in the sentence). This is
  intentionally simple keyword matching, not real NLU — documented as such
  in the chat's hint text — and only recognizes numeric quantities, not
  spelled-out numbers ("2 weeks" works, "two weeks" doesn't).
- Only the fields still missing are asked about, exactly like the Python
  agent's `missing_fields()` → the same `CLARIFYING_QUESTIONS` map ported
  from `agent.py`.
- The destination guardrail is checked before anything else, same as
  `agent.py`: if a message contains "the moon" or "narnia", the destination
  is rejected and cleared (not silently kept), so the next turn re-asks for
  it rather than getting stuck.
- Once the brief is complete, it calls the exact same `searchFlights` /
  `searchHotels` / `buildDays` functions the form mode uses — both modes
  converge on the same `state` object and the same results rendering, so
  there's one itinerary-building code path, not two.

Tested with a Node harness (mirroring the eval suite's approach) covering:
multi-turn slot-filling, not re-asking for known fields, guardrail
mid-conversation with recovery, single-message full-brief parsing, and
both numeric and word-based duration phrasing (the latter confirmed as an
intentional, documented parser limitation rather than a bug).

Accessibility for chat mode: the conversation log is `role="log"` with
`aria-live="polite"` so new agent replies are announced without stealing
focus from the input; the message field has a (visually hidden but
screen-reader-visible) `<label>`; switching modes uses the native `hidden`
attribute, which removes the inactive panel from both the visual layout
and the accessibility tree/tab order in one step, rather than juggling
`aria-hidden` and `tabindex` by hand.
