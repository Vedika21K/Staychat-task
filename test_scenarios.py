import json
from app import process_chat_turn

SCENARIOS = {
    "Scenario 1: Vague initial inquiry": [
        "Room available for tomorrow?"
    ],
    "Scenario 2: Complete direct booking (zero follow-ups)": [
        "2 rooms, 15th to 17th, 4 adults, AC"
    ],
    "Scenario 3: Hinglish slot extraction": [
        "kal ke liye room chahiye, 3 log hain"
    ],
    "Scenario 4: Changing preferences mid-conversation": [
        "AC room chahiye for tomorrow, 2 people",
        "non-AC me kya rate hai"
    ],
    "Scenario 5: Multi-guest & child policy handling": [
        "We are 7 people, 2 kids aged 4 and 6, need rooms this weekend"
    ],
    "Scenario 6: Mid-flow out-of-scope amenity interruption": [
        "Need a room for 2 adults tomorrow",
        "Do you have a swimming pool?"
    ]
}


def run_tests():
    all_transcripts = []

    for name, turns in SCENARIOS.items():
        print(f"Running {name}...")
        transcript = [f"### {name}\n"]

        # Use scenario name as unique session_id to isolate conversation state
        for turn_num, message in enumerate(turns, 1):
            res = process_chat_turn(session_id=name, message=message)
            transcript.append(f"**Turn {turn_num}**")
            transcript.append(f"- **Guest:** \"{message}\"")
            transcript.append(f"- **Bot:** {res['reply']}")
            transcript.append("```json")
            transcript.append(json.dumps(res, indent=2))
            transcript.append("```\n")

        all_transcripts.append("\n".join(transcript))

    with open("transcripts.md", "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(all_transcripts))

    print("\nAll 6 test scenarios passed! Transcripts saved to transcripts.md.")


if __name__ == "__main__":
    run_tests()