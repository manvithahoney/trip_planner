"""
Trip Planner Agent -- Gemini-powered backend.

A FastAPI server that holds one Gemini chat session per browser session,
gives the model real tools (mock_inventory via tools.py) to search flights,
hotels, and activities, and validates every itinerary Gemini produces
against the same pacing/budget rules the eval suite checks -- sending it
back for a correction if it breaks one, rather than showing the person a
broken plan.

Run locally:
    export GEMINI_API_KEY=your-key-here
    pip install -r requirements.txt
    uvicorn app:app --reload
    open http://localhost:8000

See README_DEPLOY.md for deploying this on Render.
"""

import json
import os
import re
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from google import genai
from google.genai import types

from tools import ALL_TOOLS
from validators import validate_itinerary

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
MAX_CORRECTION_ATTEMPTS = 2

# Transient errors worth retrying automatically before giving up and
# surfacing something to the person: the model being temporarily
# overloaded (503) or the account being rate-limited (429). Both are
# usually gone within a few seconds.
_TRANSIENT_MARKERS = ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"]
_RETRY_DELAYS_SEC = [2, 5, 10]


def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(marker in msg for marker in _TRANSIENT_MARKERS)


def send_with_retry(chat_session, message: str):
    """Sends a message to the Gemini chat session, retrying with backoff
    on transient errors (model overloaded / rate limited) before raising."""
    last_exc = None
    for attempt, delay in enumerate([0] + _RETRY_DELAYS_SEC):
        if delay:
            time.sleep(delay)
        try:
            return chat_session.send_message(message)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if not _is_transient_error(e):
                raise
    raise last_exc

SYSTEM_INSTRUCTION = """You are the Trip Planner Agent, a friendly multi-turn travel planning assistant.

Your job, in order:
1. Have a natural conversation to learn: destination, trip length (days),
   total budget in USD, number of travelers, and vibe (relaxing, adventurous,
   or cultural). Ask only for what's missing -- if the person gives you
   several things at once, don't re-ask for them.
2. If the destination isn't one this agent can search, call
   list_available_destinations to check, and if it's genuinely not available
   (including places that aren't real, bookable destinations -- fictional,
   off-planet, or otherwise impossible), say so plainly and warmly, and
   suggest a couple of real alternatives from the list that match what they
   seem to want. Do not invent flights or hotels for a place that isn't in
   the inventory.
3. Once you have everything, call classify_budget_tier to get the right
   tier, then call search_flights, search_hotels, and search_activities
   (all scoped to that tier) to get real options.
4. Pick one flight and one hotel from the results (mention that cheaper or
   pricier alternatives exist if relevant), and assemble a day-by-day plan:
   - relaxing = 2 activities/day, adventurous = 4/day, cultural = 3/day
   - the first and last day of any multi-day trip should have ONE FEWER
     activity than that pace, since travel/check-in and checkout eat into
     the day
   - never repeat an activity within the same trip
   - only use activities that came back from search_activities -- never
     invent one
5. When you're ready to present the finished plan, write a short, warm
   summary sentence or two, then on its own lines include a fenced code
   block starting with ```json containing the COMPLETE itinerary in
   exactly this shape:

```json
{
  "destination": "Kyoto",
  "country": "Japan",
  "duration_days": 8,
  "travelers": 2,
  "vibe": "cultural",
  "budget_tier": "luxury",
  "budget_total_usd": 6000,
  "flight": {"carrier": "...", "class": "...", "total_price_usd": 0},
  "hotel": {"name": "...", "tier": "luxury", "total_stay_usd": 0},
  "days": [
    {"day": 1, "note": "Arrival day -- lighter schedule to allow for travel/check-in.",
     "activities": [{"name": "...", "price_usd": 0}]}
  ],
  "estimated_total_cost_usd": 0
}
```

   Only include this JSON block when the plan is actually complete and
   final -- not while you're still asking questions.

If you receive a message starting with "VALIDATION_FAILED:", it means the
itinerary you just produced broke one of the rules above. Read the listed
problems, fix the itinerary, and resend a corrected ```json block along
with a brief note of what changed. Don't apologize at length -- just fix it.
"""


# One long-lived client for the whole app's lifetime, created lazily on
# first use and cached in this module-level variable -- rather than a new
# Client() per chat session, which risks the underlying HTTP client being
# torn down once the local reference that created it goes out of scope.
_CLIENT: genai.Client | None = None


def get_client() -> genai.Client:
    global _CLIENT
    if _CLIENT is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not set on the server. See README_DEPLOY.md.",
            )
        _CLIENT = genai.Client(api_key=api_key)
    return _CLIENT


# In-memory session store: session_id -> genai chat object.
# Fine for a demo; a Render free-tier restart clears it, so long-idle
# conversations may need to start over. See README_DEPLOY.md for notes
# on making this persistent if you outgrow that.
_SESSIONS: dict[str, "genai.chats.Chat"] = {}


def get_or_create_chat(session_id: str):
    if session_id not in _SESSIONS:
        client = get_client()
        _SESSIONS[session_id] = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=ALL_TOOLS,
            ),
        )
    return _SESSIONS[session_id]


def extract_json_block(text: str):
    """Pulls the last ```json ... ``` fenced block out of a reply, if any."""
    matches = re.findall(r"```json\s*([\s\S]*?)```", text)
    if not matches:
        return None, text
    raw = matches[-1].strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, text
    # Strip the JSON block out of the human-facing reply text, and collapse
    # the blank-line gap it leaves behind.
    cleaned = re.sub(r"```json\s*[\s\S]*?```", "", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return parsed, cleaned


app = FastAPI(title="Trip Planner Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    itinerary: dict | None = None
    session_id: str


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    chat_session = get_or_create_chat(session_id)

    try:
        response = send_with_retry(chat_session, req.message)
        reply_text = response.text or ""
    except Exception as e:  # noqa: BLE001 -- surface any Gemini/API error to the client
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e}")

    itinerary, reply_text = extract_json_block(reply_text)

    attempts = 0
    while itinerary is not None and attempts < MAX_CORRECTION_ATTEMPTS:
        problems = validate_itinerary(itinerary)
        if not problems:
            break
        attempts += 1
        correction_prompt = "VALIDATION_FAILED: " + " | ".join(problems)
        try:
            response = send_with_retry(chat_session, correction_prompt)
            reply_text = response.text or ""
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Gemini API error during correction: {e}")
        itinerary, reply_text = extract_json_block(reply_text)

    return ChatResponse(reply=reply_text, itinerary=itinerary, session_id=session_id)


@app.get("/api/health")
def health():
    return {"ok": True, "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY"))}


@app.get("/")
def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
