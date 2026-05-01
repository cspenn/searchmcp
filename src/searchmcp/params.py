"""Search parameter model for DDGS search operations."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

type SafeSearch = Literal["off", "moderate", "strict"]
type Timelimit = Literal["d", "w", "m", "y"]


class SearchParams(BaseModel):
    """Validated, immutable DDGS search parameters."""

    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)

    max_results: Annotated[int, Field(ge=1, le=100)] = 10
    region: str = "wt-wt"
    safesearch: SafeSearch = "moderate"
    timelimit: Timelimit | None = None
    backend: str = "auto"
    page: Annotated[int, Field(ge=1, le=100)] = 1
