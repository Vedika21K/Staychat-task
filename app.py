import json
import warnings
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from state import ConversationGraphState
from agent import booking_workflow

warnings.filterwarnings("ignore")
load_dotenv()

app = Flask(__name__)
SESSIONS: dict[str, ConversationGraphState] = {}


def process_chat_turn(session_id: str, message: str) -> dict:
    current_state = SESSIONS.get(session_id, ConversationGraphState())
    current_state.user_message = message

    # Execute LangGraph execution flow
    output_state_dict = booking_workflow.invoke(current_state)
    updated_state = ConversationGraphState(**output_state_dict)
    SESSIONS[session_id] = updated_state

    return {
        "reply": updated_state.reply,
        "state": {
            "check_in_date": updated_state.check_in_date,
            "check_out_date": updated_state.check_out_date,
            "adults": updated_state.adults,
            "children": updated_state.children,
            "rooms_needed": updated_state.rooms_needed,
            "ac_preference": updated_state.ac_preference,
            "special_requests": updated_state.special_requests
        },
        "status": updated_state.status
    }


@app.route("/chat", methods=["POST"])
def chat():
    """
    POST payload:
    {
        "session_id": "optional_id",
        "message": "kal ke liye 2 room chahiye AC wala"
    }
    """
    data = request.get_json(force=True)
    session_id = data.get("session_id", "default_session")
    message = data.get("message", "")

    result = process_chat_turn(session_id, message)
    return jsonify(result)


def run_cli():
    print("=" * 60)
    print("StayChat Bot (LangGraph Powered) - CLI Mode")
    print("=" * 60)
    session_id = "cli_session"
    while True:
        try:
            msg = input("\nGuest: ").strip()
            if not msg or msg.lower() in ("exit", "quit"):
                break
            res = process_chat_turn(session_id, msg)
            print(f"\nBot: {res['reply']}")
            print("\nTurn JSON Payload:")
            print(json.dumps(res, indent=2))
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        print("Running Flask API on http://127.0.0.1:5000/chat ...")
        app.run(port=5000, debug=False)
    else:
        run_cli()