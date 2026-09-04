import os
import json
import itertools
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

with open("inventory.json", "r") as f:
    INVENTORY = json.load(f)

HOTEL_NAME = INVENTORY.get("hotel_name") or INVENTORY.get("hotel name", "Hotel Sahu")
CURRENCY = INVENTORY.get("currency", "INR")
MODEL_NAME = "gemini-3.6-flash"

class BookingState(BaseModel):
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = 0
    child_ages: List[int] = Field(default_factory=list)
    num_rooms: Optional[int] = None
    ac_preference: Optional[bool] = None
    special_requests: Optional[str] = None

def calculate_nights(check_in: str, check_out: str) -> int:
    try:
        d1 = datetime.strptime(check_in, "%Y-%m-%d")
        d2 = datetime.strptime(check_out, "%Y-%m-%d")
        delta = (d2 - d1).days
        return max(1, delta)
    except Exception:
        return 1

def calculate_recommendations(state: BookingState):
    if not state.check_in_date or not state.check_out_date:
        return []
    
    nights = calculate_nights(state.check_in_date, state.check_out_date)
    
    policies = INVENTORY.get("policies", {})
    children_free = policies.get("children_under_5_free") or policies.get("children_under 5 free", False)

    billable_children = 0
    if children_free:
        if state.child_ages:
            billable_children = sum(1 for age in state.child_ages if age >= 5)
        else:
            billable_children = state.children or 0
    else:
        billable_children = state.children or 0
    
    total_guests = (state.adults or 1) + billable_children
    eligible_rooms = [
        r for r in INVENTORY.get("rooms", [])
        if state.ac_preference is None or ("AC" in r["type"] and "Non-AC" not in r["type"]) == state.ac_preference
    ]

    combos = []
    if state.num_rooms:
        room_counts = [state.num_rooms]
    elif total_guests <= 3:
        room_counts = [1]
    elif total_guests <= 6:
        room_counts = [1, 2]
    else:
        room_counts = [2, 3]

    for count in room_counts:
        for room_tuple in itertools.combinations_with_replacement(eligible_rooms, count):
            max_cap = sum(r["max_occupancy"] for r in room_tuple)
            if max_cap >= total_guests:
                base_cap = sum(r["base_occupancy"] for r in room_tuple)
                extra_guests = max(0, total_guests - base_cap)
                
                extra_rate = max(r.get("extra_guest_price", 0) for r in room_tuple) if extra_guests > 0 else 0
                base_price = sum(r["base_price"] for r in room_tuple)
                
                nightly_price = base_price + (extra_guests * extra_rate)
                total_price = nightly_price * nights
                
                counts = {}
                for r in room_tuple:
                    counts[r["type"]] = counts.get(r["type"], 0) + 1
                name_str = " + ".join(f"{cnt}x {rtype}" for rtype, cnt in counts.items())
                
                combos.append({
                    "num_rooms": count,
                    "room_name": name_str,
                    "total_price": total_price,
                    "currency": CURRENCY,
                    "breakdown": f"{count} room(s), {nights} night(s), accommodates up to {max_cap} guests"
                })

    combos.sort(key=lambda x: (x["num_rooms"], x["total_price"]))
    
    seen = set()
    unique_recs = []
    for c in combos:
        if c["room_name"] not in seen:
            seen.add(c["room_name"])
            unique_recs.append(c)
            if len(unique_recs) == 3:
                break
                
    return unique_recs

def extract_slots(client: genai.Client, user_message: str, current_state: BookingState, history: list) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d, %A")
    prompt = f"""You are a strict NLU slot-extraction engine for a hotel booking assistant.
Current Date: {today_str}
Conversation History: {history}
Current Known State: {current_state.model_dump_json()}
User Message: "{user_message}"

Extract details mentioned in the user message. Support English and Hinglish. 
If the user specifies a check-in date or 'tomorrow/kal' but omits check-out date or duration, extract check_in, and leave check_out as null so the bot can ask for the duration or checkout date.
If the user wants to cancel, restart, or change context completely, set "reset_state" to true.
Respond ONLY with a valid JSON object matching this exact structure:
{{
  "check_in": string (YYYY-MM-DD format) or null,
  "check_out": string (YYYY-MM-DD format) or null,
  "adults": int or null,
  "children": int or null,
  "child_ages": [int, ...] or [],
  "num_rooms": int or null,
  "ac_preference": true or false or null,
  "special_requests": string or null,
  "out_of_scope_query": string or null,
  "user_confirms": true or false,
  "reset_state": true or false
}}
"""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.NONE
                    )
                )
            )
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"Gemini NLU error: {e}")
        return {}

def process_turn(client: genai.Client, user_message: str, current_state: BookingState, conversation_history: list):
    extracted = extract_slots(client, user_message, current_state, conversation_history)

    if extracted.get("reset_state"):
        current_state = BookingState()
        reply = f"Let's start over. How can I help you with your booking at {HOTEL_NAME}?"
        return reply, current_state, "gathering"

    if extracted.get("check_in"): current_state.check_in_date = extracted["check_in"]
    if extracted.get("check_out"): current_state.check_out_date = extracted["check_out"]
    if extracted.get("adults") is not None: current_state.adults = extracted["adults"]
    if extracted.get("children") is not None: current_state.children = extracted["children"]
    if extracted.get("child_ages"): current_state.child_ages = extracted["child_ages"]
    if extracted.get("num_rooms") is not None: current_state.num_rooms = extracted["num_rooms"]
    if extracted.get("ac_preference") is not None: current_state.ac_preference = extracted["ac_preference"]
    if extracted.get("special_requests"): current_state.special_requests = extracted["special_requests"]

    has_dates = bool(current_state.check_in_date and current_state.check_out_date)
    has_guests = bool(current_state.adults)
    out_of_scope = extracted.get("out_of_scope_query")

    if extracted.get("user_confirms"):
        status = "confirmed"
        reply = f"Thank you! Your booking at {HOTEL_NAME} has been confirmed."
        return reply, current_state, status

    if not has_dates or not has_guests:
        status = "gathering"
        missing = []
        if not has_dates: missing.append("check-in and check-out dates (or duration)")
        if not has_guests: missing.append("number of adult guests")

        reply_prompt = f"""Hotel: {HOTEL_NAME}.
User Message: "{user_message}"
Missing details: {missing}
Out of scope question: {out_of_scope}
Policies & Amenities: {INVENTORY.get('policies', {})}

Rules:
- Respond naturally in English or Hinglish matching the guest's language.
- If the guest asked about an amenity/service not explicitly listed in hotel policies or room features, state clearly that the hotel does not provide it.
- Ask ONLY for the missing details. Never re-ask details we already know. Keep it brief.
"""
    else:
        status = "recommending"
        recommendations = calculate_recommendations(current_state)
        
        reply_prompt = f"""User Message: "{user_message}"
Out of scope question: {out_of_scope}
Programmatically Calculated Options: {recommendations}
Policies: {INVENTORY.get('policies', {})}

Rules:
- Respond naturally matching the guest's language (English or Hinglish).
- Present the calculated room options clearly with their exact total prices in {CURRENCY}.
- If an out-of-scope query was asked, state whether the hotel offers it based strictly on policies.
- Do not modify prices or invent unlisted rooms.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=reply_prompt,
            config=types.GenerateContentConfig(
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.NONE
                    )
                )
            )
        )
        reply = response.text.strip()
    except Exception as e:
        print(f"Gemini Response error: {e}")
        reply = "I am processing your request. Could you please confirm your details?"

    return reply, current_state, status

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set in .env file.")
        return

    client = genai.Client(api_key=api_key)
    state = BookingState()
    history = []

    print(f"=== {HOTEL_NAME} Booking CLI Started (type 'exit' to quit) ===\n")

    while True:
        try:
            user_input = input("Guest: ")
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.strip().lower() in ["exit", "quit"]:
            break

        reply, state, status = process_turn(client, user_input, state, history)
        history.append(f"Guest: {user_input}")
        history.append(f"Bot: {reply}")

        print(f"\nBot: {reply}\n")
        print("Structured State Output:")
        print(json.dumps({
            "status": status,
            "state": state.model_dump()
        }, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    main()