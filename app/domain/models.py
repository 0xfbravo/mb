from typing import Optional

from pydantic import BaseModel


class Pagination(BaseModel):
    """Pagination model"""

    total: int
    page: int
    next_page: Optional[int] = None
    prev_page: Optional[int] = None

    def to_presentation(self) -> dict:
        """Convert the pagination model to a presentation layer model"""
        return {
            "total": self.total,
            "page": self.page,
            "next_page": self.next_page,
            "prev_page": self.prev_page,
        }
