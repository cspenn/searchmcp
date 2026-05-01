"""Tests for src/searchmcp/params.py — SearchParams model."""

import pytest
from pydantic import ValidationError

from searchmcp.params import SearchParams


class TestSearchParams:
    """Tests for the SearchParams Pydantic model."""

    # ------------------------------------------------------------------
    # 1. Default values
    # ------------------------------------------------------------------

    def test_defaults(self) -> None:
        """SearchParams() produces correct default field values."""
        p = SearchParams()
        assert p.max_results == 10
        assert p.region == "wt-wt"
        assert p.safesearch == "moderate"
        assert p.timelimit is None
        assert p.backend == "auto"
        assert p.page == 1

    # ------------------------------------------------------------------
    # 2. Valid safesearch values
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("value", ["off", "moderate", "strict"])
    def test_valid_safesearch(self, value: str) -> None:
        """All three SafeSearch literals are accepted."""
        p = SearchParams(safesearch=value)
        assert p.safesearch == value

    def test_invalid_safesearch(self) -> None:
        """A string outside the SafeSearch literal raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(safesearch="unknown")  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # 3. Valid timelimit values (and None)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("value", ["d", "w", "m", "y"])
    def test_valid_timelimit(self, value: str) -> None:
        """All four Timelimit literals are accepted."""
        p = SearchParams(timelimit=value)
        assert p.timelimit == value

    def test_timelimit_none(self) -> None:
        """timelimit=None is the default and can be set explicitly."""
        p = SearchParams(timelimit=None)
        assert p.timelimit is None

    def test_invalid_timelimit(self) -> None:
        """A string outside the Timelimit literal raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(timelimit="x")  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # 4. max_results bounds
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("value", [1, 100])
    def test_max_results_boundary_valid(self, value: int) -> None:
        """Boundary values 1 and 100 are valid for max_results."""
        p = SearchParams(max_results=value)
        assert p.max_results == value

    @pytest.mark.parametrize("value", [0, 101])
    def test_max_results_boundary_invalid(self, value: int) -> None:
        """Values 0 and 101 are outside the allowed range and raise ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(max_results=value)

    # ------------------------------------------------------------------
    # 5. page bounds
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("value", [1, 100])
    def test_page_boundary_valid(self, value: int) -> None:
        """Boundary values 1 and 100 are valid for page."""
        p = SearchParams(page=value)
        assert p.page == value

    @pytest.mark.parametrize("value", [0, 101])
    def test_page_boundary_invalid(self, value: int) -> None:
        """Values 0 and 101 are outside the allowed range and raise ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(page=value)

    # ------------------------------------------------------------------
    # 6. extra="ignore" — unknown fields are silently dropped
    # ------------------------------------------------------------------

    def test_extra_fields_ignored(self) -> None:
        """Extra keyword arguments are silently ignored (extra='ignore')."""
        p = SearchParams(unknown_field=42)  # type: ignore[call-arg]
        # Object is constructed without error and has correct defaults.
        assert p.max_results == 10

    # ------------------------------------------------------------------
    # 7. frozen=True — mutation raises after construction
    # ------------------------------------------------------------------

    def test_frozen_raises_on_mutation(self) -> None:
        """Setting a field on a frozen model raises ValidationError or AttributeError."""
        p = SearchParams()
        with pytest.raises((ValidationError, AttributeError)):
            p.max_results = 99  # type: ignore[misc]

    # ------------------------------------------------------------------
    # 8. strict=True — string coercion for int fields is rejected
    # ------------------------------------------------------------------

    def test_strict_rejects_string_for_max_results(self) -> None:
        """strict=True means passing '10' (str) instead of 10 (int) raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(max_results="10")  # type: ignore[arg-type]

    def test_strict_rejects_string_for_page(self) -> None:
        """strict=True means passing '1' (str) instead of 1 (int) raises ValidationError."""
        with pytest.raises(ValidationError):
            SearchParams(page="1")  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # 9. Successful full construction with non-default values
    # ------------------------------------------------------------------

    def test_full_construction(self) -> None:
        """All fields can be set to non-default valid values."""
        p = SearchParams(
            max_results=50,
            region="us-en",
            safesearch="strict",
            timelimit="w",
            backend="google",
            page=5,
        )
        assert p.max_results == 50
        assert p.region == "us-en"
        assert p.safesearch == "strict"
        assert p.timelimit == "w"
        assert p.backend == "google"
        assert p.page == 5
