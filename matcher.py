import json
from itertools import combinations_with_replacement
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class RoomAllocation(BaseModel):
    room_type: str
    is_ac: bool
    base_price: int
    extra_guest_price: int
    allocated_guests: int
    nightly_price: int


class Recommendation(BaseModel):
    description: str
    rooms: List[RoomAllocation]
    total_rooms: int
    nights: int
    total_price: int
    currency: str


class InventoryMatcher:
    def __init__(self, inventory_path: str = "inventory.json"):
        with open(inventory_path, "r", encoding="utf-8") as f:
            self.inventory = json.load(f)
        self.rooms = self.inventory.get("rooms", [])
        self.policies = self.inventory.get("policies", {})
        self.currency = self.inventory.get("currency", "INR")

    def _calculate_nights(self, check_in: Optional[str], check_out: Optional[str]) -> int:
        """Calculates total nights. Defaults to 1 night if check_out is unspecified."""
        if not check_in or not check_out:
            return 1
        try:
            d1 = datetime.strptime(check_in, "%Y-%m-%d")
            d2 = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (d2 - d1).days
            return max(nights, 1)
        except ValueError:
            return 1

    def _get_chargeable_guests(self, adults: int, children: List[int]) -> int:
        """
        Deducts children under 5 years of age based on hotel policy.
        """
        chargeable_children = 0
        under_5_free = self.policies.get("children_under_5_free", False)

        for age in children:
            if under_5_free and age < 5:
                continue
            chargeable_children += 1

        return adults + chargeable_children

    def _calculate_combo_price(self, combo: List[Dict[str, Any]], total_guests: int, nights: int) -> Optional[Dict[str, Any]]:
        """
        Distributes guests greedily across selected rooms up to max_occupancy
        and computes total price based on base price + extra guest charges.
        """
        total_max_capacity = sum(r["max_occupancy"] for r in combo)
        if total_guests > total_max_capacity:
            return None

        # Sort rooms descending by base_occupancy to fill larger capacities first
        sorted_rooms = sorted(combo, key=lambda r: r["base_occupancy"], reverse=True)
        remaining_guests = total_guests
        allocations: List[RoomAllocation] = []
        nightly_combo_total = 0

        # Step 1: Allocate base occupancy
        assigned = []
        for r in sorted_rooms:
            base_allocated = min(remaining_guests, r["base_occupancy"])
            remaining_guests -= base_allocated
            assigned.append({"room": r, "count": base_allocated})

        # Step 2: Allocate extra guests up to max_occupancy
        for entry in assigned:
            r = entry["room"]
            current_allocated = entry["count"]
            room_max = r["max_occupancy"]
            can_add = min(remaining_guests, room_max - current_allocated)
            entry["count"] += can_add
            remaining_guests -= can_add

            # Step 3: Compute price per room
            base_p = r["base_price"]
            extra_count = max(0, entry["count"] - r["base_occupancy"])
            room_cost = base_p + (extra_count * r.get("extra_guest_price", 0))
            nightly_combo_total += room_cost

            allocations.append(
                RoomAllocation(
                    room_type=r["type"],
                    is_ac=r.get("is_ac", "AC" in r.get("type", "") and "Non-AC" not in r.get("type", "")),
                    base_price=base_p,
                    extra_guest_price=r.get("extra_guest_price", 0),
                    allocated_guests=entry["count"],
                    nightly_price=room_cost
                )
            )

        if remaining_guests > 0:
            return None

        total_price = nightly_combo_total * nights

        # Summarize description (e.g., '2x Deluxe Double AC' or '1x Standard Non-AC')
        counts: Dict[str, int] = {}
        for r in allocations:
            counts[r.room_type] = counts.get(r.room_type, 0) + 1
        desc_parts = [f"{count}x {name}" for name, count in counts.items()]
        description = " + ".join(desc_parts)

        return {
            "description": description,
            "rooms": allocations,
            "total_rooms": len(combo),
            "nights": nights,
            "total_price": total_price,
            "currency": self.currency
        }

    def find_recommendations(
        self,
        adults: int,
        children: Optional[List[int]] = None,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        ac_preference: Optional[bool] = None,
        rooms_needed: Optional[int] = None,
        max_options: int = 3
    ) -> List[Recommendation]:
        """
        Finds and ranks at most 3 room combinations matching the constraints.
        """
        if children is None:
            children = []

        total_chargeable = self._get_chargeable_guests(adults, children)
        nights = self._calculate_nights(check_in_date, check_out_date)

        # Filter candidate rooms by AC preference if explicitly set
        candidate_rooms = self.rooms
        if ac_preference is not None:
            candidate_rooms = [r for r in self.rooms if r.get("is_ac") == ac_preference]
            # Fallback to all rooms if filter eliminates entire inventory
            if not candidate_rooms:
                candidate_rooms = self.rooms

        # Determine combo sizes: if user specified rooms_needed, fix size; else test sizes 1 to 3
        if rooms_needed:
            room_counts = [rooms_needed]
        else:
            # Estimate room count needed (assumes max room capacity of 6)
            min_rooms = max(1, (total_chargeable + 5) // 6)
            room_counts = list(range(min_rooms, min_rooms + 2))

        valid_combos = []
        seen_descriptions = set()

        for k in room_counts:
            for combo in combinations_with_replacement(candidate_rooms, k):
                result = self._calculate_combo_price(list(combo), total_chargeable, nights)
                if result and result["description"] not in seen_descriptions:
                    seen_descriptions.add(result["description"])
                    valid_combos.append(Recommendation(**result))

        # Rank combinations: prioritize lowest total price, then fewest rooms
        valid_combos.sort(key=lambda x: (x.total_price, x.total_rooms))

        return valid_combos[:max_options]