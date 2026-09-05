### Scenario 1: Vague initial inquiry

**Turn 1**
- **Guest:** "Room available for tomorrow?"
- **Bot:** Could you please share your number of guests (adults)?
```json
{
  "reply": "Could you please share your number of guests (adults)?",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": null,
    "children": [],
    "rooms_needed": null,
    "ac_preference": null,
    "special_requests": []
  },
  "status": "gathering"
}
```


---

### Scenario 2: Complete direct booking (zero follow-ups)

**Turn 1**
- **Guest:** "2 rooms, 15th to 17th, 4 adults, AC"
- **Bot:** Here are our best available options:
Option 1: 2x Standard Non-AC — INR 6,000 total (2 nights)
Option 2: 1x Standard Non-AC + 1x Deluxe Double AC — INR 8,000 total (2 nights)
Option 3: 1x Standard Non-AC + 1x Super Deluxe AC — INR 10,000 total (2 nights)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 2x Standard Non-AC \u2014 INR 6,000 total (2 nights)\nOption 2: 1x Standard Non-AC + 1x Deluxe Double AC \u2014 INR 8,000 total (2 nights)\nOption 3: 1x Standard Non-AC + 1x Super Deluxe AC \u2014 INR 10,000 total (2 nights)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-15",
    "check_out_date": "2026-09-17",
    "adults": 4,
    "children": [],
    "rooms_needed": 2,
    "ac_preference": true,
    "special_requests": []
  },
  "status": "recommending"
}
```


---

### Scenario 3: Hinglish slot extraction

**Turn 1**
- **Guest:** "kal ke liye room chahiye, 3 log hain"
- **Bot:** Here are our best available options:
Option 1: 1x Standard Non-AC — INR 2,000 total (1 night)
Option 2: 2x Standard Non-AC — INR 3,000 total (1 night)
Option 3: 1x Deluxe Double AC — INR 3,200 total (1 night)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 1x Standard Non-AC \u2014 INR 2,000 total (1 night)\nOption 2: 2x Standard Non-AC \u2014 INR 3,000 total (1 night)\nOption 3: 1x Deluxe Double AC \u2014 INR 3,200 total (1 night)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": 3,
    "children": [],
    "rooms_needed": null,
    "ac_preference": null,
    "special_requests": []
  },
  "status": "recommending"
}
```


---

### Scenario 4: Changing preferences mid-conversation

**Turn 1**
- **Guest:** "AC room chahiye for tomorrow, 2 people"
- **Bot:** Here are our best available options:
Option 1: 1x Standard Non-AC — INR 1,500 total (1 night)
Option 2: 1x Deluxe Double AC — INR 2,500 total (1 night)
Option 3: 2x Standard Non-AC — INR 3,000 total (1 night)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 1x Standard Non-AC \u2014 INR 1,500 total (1 night)\nOption 2: 1x Deluxe Double AC \u2014 INR 2,500 total (1 night)\nOption 3: 2x Standard Non-AC \u2014 INR 3,000 total (1 night)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": 2,
    "children": [],
    "rooms_needed": null,
    "ac_preference": true,
    "special_requests": []
  },
  "status": "recommending"
}
```

**Turn 2**
- **Guest:** "non-AC me kya rate hai"
- **Bot:** Here are our best available options:
Option 1: 1x Standard Non-AC — INR 1,500 total (1 night)
Option 2: 1x Deluxe Double AC — INR 2,500 total (1 night)
Option 3: 2x Standard Non-AC — INR 3,000 total (1 night)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 1x Standard Non-AC \u2014 INR 1,500 total (1 night)\nOption 2: 1x Deluxe Double AC \u2014 INR 2,500 total (1 night)\nOption 3: 2x Standard Non-AC \u2014 INR 3,000 total (1 night)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": 2,
    "children": [],
    "rooms_needed": null,
    "ac_preference": false,
    "special_requests": []
  },
  "status": "recommending"
}
```


---

### Scenario 5: Multi-guest & child policy handling

**Turn 1**
- **Guest:** "We are 7 people, 2 kids aged 4 and 6, need rooms this weekend"
- **Bot:** Here are our best available options:
Option 1: 3x Standard Non-AC — INR 11,000 total (2 nights)
Option 2: 2x Standard Non-AC + 1x Deluxe Double AC — INR 13,000 total (2 nights)
Option 3: 2x Standard Non-AC + 1x Super Deluxe AC — INR 15,000 total (2 nights)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 3x Standard Non-AC \u2014 INR 11,000 total (2 nights)\nOption 2: 2x Standard Non-AC + 1x Deluxe Double AC \u2014 INR 13,000 total (2 nights)\nOption 3: 2x Standard Non-AC + 1x Super Deluxe AC \u2014 INR 15,000 total (2 nights)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-05",
    "check_out_date": "2026-09-07",
    "adults": 7,
    "children": [
      4,
      6
    ],
    "rooms_needed": null,
    "ac_preference": null,
    "special_requests": []
  },
  "status": "recommending"
}
```


---

### Scenario 6: Mid-flow out-of-scope amenity interruption

**Turn 1**
- **Guest:** "Need a room for 2 adults tomorrow"
- **Bot:** Here are our best available options:
Option 1: 1x Standard Non-AC — INR 1,500 total (1 night)
Option 2: 1x Deluxe Double AC — INR 2,500 total (1 night)
Option 3: 1x Super Deluxe AC — INR 3,500 total (1 night)

Let me know which option suits you best!
```json
{
  "reply": "Here are our best available options:\nOption 1: 1x Standard Non-AC \u2014 INR 1,500 total (1 night)\nOption 2: 1x Deluxe Double AC \u2014 INR 2,500 total (1 night)\nOption 3: 1x Super Deluxe AC \u2014 INR 3,500 total (1 night)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": 2,
    "children": [],
    "rooms_needed": 1,
    "ac_preference": null,
    "special_requests": []
  },
  "status": "recommending"
}
```

**Turn 2**
- **Guest:** "Do you have a swimming pool?"
- **Bot:** Please note that we do not offer swimming pool facilities. However, we'd love to help you book your stay!

Here are our best available options:
Option 1: 1x Standard Non-AC — INR 1,500 total (1 night)
Option 2: 1x Deluxe Double AC — INR 2,500 total (1 night)
Option 3: 1x Super Deluxe AC — INR 3,500 total (1 night)

Let me know which option suits you best!
```json
{
  "reply": "Please note that we do not offer swimming pool facilities. However, we'd love to help you book your stay!\n\nHere are our best available options:\nOption 1: 1x Standard Non-AC \u2014 INR 1,500 total (1 night)\nOption 2: 1x Deluxe Double AC \u2014 INR 2,500 total (1 night)\nOption 3: 1x Super Deluxe AC \u2014 INR 3,500 total (1 night)\n\nLet me know which option suits you best!",
  "state": {
    "check_in_date": "2026-09-06",
    "check_out_date": null,
    "adults": 2,
    "children": [],
    "rooms_needed": 1,
    "ac_preference": null,
    "special_requests": []
  },
  "status": "recommending"
}
```
