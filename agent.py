import os
import warnings
from datetime import datetime
from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from state import ConversationGraphState, ExtractedDelta
from matcher import InventoryMatcher

from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore")

# Initialize deterministic matcher
matcher = InventoryMatcher(inventory_path="inventory.json")

# Initialize LangChain LLM with structured output
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.1,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
extractor = llm.with_structured_output(ExtractedDelta)


# --- Node 1: NLU & Entity Extraction ---
def extract_nlu_node(state: ConversationGraphState) -> Dict[str, Any]:
    ref_date = datetime.now().strftime("%Y-%m-%d (%A)")

    system_prompt = f"""
You are the NLU parser for {matcher.inventory.get('hotel_name', 'our hotel')}.
Extract booking updates from the guest's message into structured JSON.
Today's reference date: {ref_date}.

Rules:
- Handle English and Hinglish smoothly.
- 'kal' / 'kal ke liye' -> tomorrow's date relative to {ref_date}.
- 'parso' -> day after tomorrow.
- 'log' / 'jan' / 'adults' -> adults.
- 'bacche' / 'kids' -> children.
- 'AC wala' -> ac_preference = true.
- 'non-AC' / 'bina AC' -> ac_preference = false.
- Out of scope: swimming pool, taxi, spa, gym, refunds.
"""

    delta: ExtractedDelta = extractor.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.user_message)
    ])

    updates: Dict[str, Any] = {}
    if delta.check_in_date is not None:
        updates["check_in_date"] = delta.check_in_date
    if delta.check_out_date is not None:
        updates["check_out_date"] = delta.check_out_date
    if delta.adults is not None:
        updates["adults"] = delta.adults
    if delta.children is not None:
        updates["children"] = delta.children
    if delta.rooms_needed is not None:
        updates["rooms_needed"] = delta.rooms_needed
    if delta.ac_preference is not None:
        updates["ac_preference"] = delta.ac_preference
    if delta.special_requests:
        updates["special_requests"] = list(set(state.special_requests + delta.special_requests))

    updates["out_of_scope_query"] = delta.out_of_scope_query
    return updates


# --- Node 2: Deterministic Business Logic & Response Node ---
def decision_node(state: ConversationGraphState) -> Dict[str, Any]:
    policy_notice = ""
    if state.out_of_scope_query:
        policy_notice = (
            f"Please note that we do not offer {state.out_of_scope_query} facilities. "
            f"However, we'd love to help you book your stay!\n\n"
        )

    # Check for missing critical info
    if not state.has_sufficient_info():
        missing = []
        if not state.check_in_date:
            missing.append("check-in date")
        if not state.adults:
            missing.append("number of guests (adults)")
        return {
            "status": "gathering",
            "reply": f"{policy_notice}Could you please share your {' and '.join(missing)}?"
        }

    # Deterministic matching using matcher.py
    recs = matcher.find_recommendations(
        adults=state.adults,
        children=state.children,
        check_in_date=state.check_in_date,
        check_out_date=state.check_out_date,
        ac_preference=state.ac_preference,
        rooms_needed=state.rooms_needed,
        max_options=3
    )

    if not recs:
        return {
            "status": "recommending",
            "reply": f"{policy_notice}No room configurations matched your exact criteria. Would you like to adjust dates or preferences?"
        }

    lines = [
        f"Option {i}: {r.description} — {r.currency} {r.total_price:,} total ({r.nights} night{'s' if r.nights > 1 else ''})"
        for i, r in enumerate(recs, 1)
    ]
    reply_text = (
        f"{policy_notice}Here are our best available options:\n"
        + "\n".join(lines)
        + "\n\nLet me know which option suits you best!"
    )

    return {
        "status": "recommending",
        "reply": reply_text
    }


# --- Build Graph ---
graph_builder = StateGraph(ConversationGraphState)
graph_builder.add_node("extract_nlu", extract_nlu_node)
graph_builder.add_node("decision_node", decision_node)

graph_builder.set_entry_point("extract_nlu")
graph_builder.add_edge("extract_nlu", "decision_node")
graph_builder.add_edge("decision_node", END)

booking_workflow = graph_builder.compile()