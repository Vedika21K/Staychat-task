from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ExtractedDelta(BaseModel):
    """Schema for LLM structured extraction per turn."""
    check_in_date: Optional[str] = Field(
        default=None, description="Check-in date formatted as YYYY-MM-DD"
    )
    check_out_date: Optional[str] = Field(
        default=None, description="Check-out date formatted as YYYY-MM-DD"
    )
    adults: Optional[int] = Field(
        default=None, description="Total number of adults"
    )
    children: Optional[List[int]] = Field(
        default=None, description="List of children ages (e.g. [4, 6])"
    )
    rooms_needed: Optional[int] = Field(
        default=None, description="Total rooms requested by guest"
    )
    ac_preference: Optional[bool] = Field(
        default=None, description="True for AC, False for Non-AC, None if unspecified"
    )
    special_requests: Optional[List[str]] = Field(
        default=None, description="Special requests mentioned"
    )
    out_of_scope_query: Optional[str] = Field(
        default=None,
        description="Mention of pool, taxi, gym, pets, or amenities outside room inventory"
    )
    user_intent: str = Field(
        default="inquiry",
        description="'inquiry', 'modify', 'confirm', or 'chitchat'"
    )


class ConversationGraphState(BaseModel):
    """LangGraph unified state."""
    user_message: str = ""
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    adults: Optional[int] = None
    children: List[int] = Field(default_factory=list)
    rooms_needed: Optional[int] = None
    ac_preference: Optional[bool] = None
    special_requests: List[str] = Field(default_factory=list)
    status: Literal["gathering", "recommending", "confirmed"] = "gathering"
    out_of_scope_query: Optional[str] = None
    reply: str = ""

    def has_sufficient_info(self) -> bool:
        return bool(self.check_in_date and self.adults and self.adults > 0)