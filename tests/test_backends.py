"""Tests for src/searchmcp/backends.py — ENGINE_REGISTRY, SPECIAL, validate_backend."""

import pytest

from searchmcp.backends import ENGINE_REGISTRY, SPECIAL, validate_backend


class TestEngineRegistry:
    """Tests for the ENGINE_REGISTRY constant and SPECIAL set."""

    def test_registry_has_exactly_five_keys(self) -> None:
        """ENGINE_REGISTRY must contain exactly 5 category keys."""
        assert set(ENGINE_REGISTRY.keys()) == {
            "text",
            "news",
            "images",
            "videos",
            "books",
        }

    @pytest.mark.parametrize("category", ["text", "news", "images", "videos", "books"])
    def test_registry_values_are_frozensets(self, category: str) -> None:
        """Every value in ENGINE_REGISTRY is a frozenset."""
        assert isinstance(ENGINE_REGISTRY[category], frozenset)

    def test_bing_not_in_text(self) -> None:
        """'bing' must NOT be in the text category (disabled in DDGS v9.10.0)."""
        assert "bing" not in ENGINE_REGISTRY["text"]

    def test_special_contains_auto_and_all(self) -> None:
        """SPECIAL frozenset must contain both 'auto' and 'all'."""
        assert "auto" in SPECIAL
        assert "all" in SPECIAL

    def test_special_is_frozenset(self) -> None:
        """SPECIAL must be a frozenset."""
        assert isinstance(SPECIAL, frozenset)

    # Registry membership spot-checks
    def test_text_backends_present(self) -> None:
        """text category includes the expected backends."""
        expected = {
            "brave",
            "duckduckgo",
            "google",
            "mojeek",
            "wikipedia",
            "grokipedia",
            "yahoo",
            "yandex",
        }
        assert expected == ENGINE_REGISTRY["text"]

    def test_news_backends_present(self) -> None:
        """news category includes exactly bing, duckduckgo, yahoo."""
        assert ENGINE_REGISTRY["news"] == frozenset({"bing", "duckduckgo", "yahoo"})

    def test_images_backend_present(self) -> None:
        """images category contains only duckduckgo."""
        assert ENGINE_REGISTRY["images"] == frozenset({"duckduckgo"})

    def test_videos_backend_present(self) -> None:
        """videos category contains only duckduckgo."""
        assert ENGINE_REGISTRY["videos"] == frozenset({"duckduckgo"})

    def test_books_backend_present(self) -> None:
        """books category contains only annasarchive."""
        assert ENGINE_REGISTRY["books"] == frozenset({"annasarchive"})


class TestValidateBackend:
    """Tests for validate_backend()."""

    # ------------------------------------------------------------------
    # 1 & 2. All categories accept "auto" and "all"
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("category", ["text", "news", "images", "videos", "books"])
    def test_auto_valid_for_all_categories(self, category: str) -> None:
        """'auto' is accepted as valid for every category."""
        result = validate_backend(category, "auto")
        assert result == "auto"

    @pytest.mark.parametrize("category", ["text", "news", "images", "videos", "books"])
    def test_all_valid_for_all_categories(self, category: str) -> None:
        """'all' is accepted as valid for every category."""
        result = validate_backend(category, "all")
        assert result == "all"

    # ------------------------------------------------------------------
    # 3. text category — individual valid backends
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "backend",
        [
            "brave",
            "duckduckgo",
            "google",
            "mojeek",
            "wikipedia",
            "grokipedia",
            "yahoo",
            "yandex",
        ],
    )
    def test_text_accepts_valid_backends(self, backend: str) -> None:
        """Each backend in the text category is individually accepted."""
        assert validate_backend("text", backend) == backend

    # ------------------------------------------------------------------
    # 4. news category — individual valid backends
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("backend", ["bing", "duckduckgo", "yahoo"])
    def test_news_accepts_valid_backends(self, backend: str) -> None:
        """Each backend in the news category is individually accepted."""
        assert validate_backend("news", backend) == backend

    # ------------------------------------------------------------------
    # 5 & 6. images and videos
    # ------------------------------------------------------------------

    def test_images_accepts_duckduckgo(self) -> None:
        """images category accepts 'duckduckgo'."""
        assert validate_backend("images", "duckduckgo") == "duckduckgo"

    def test_videos_accepts_duckduckgo(self) -> None:
        """videos category accepts 'duckduckgo'."""
        assert validate_backend("videos", "duckduckgo") == "duckduckgo"

    # ------------------------------------------------------------------
    # 7. books category
    # ------------------------------------------------------------------

    def test_books_accepts_annasarchive(self) -> None:
        """books category accepts 'annasarchive'."""
        assert validate_backend("books", "annasarchive") == "annasarchive"

    # ------------------------------------------------------------------
    # 8. Comma-separated valid list
    # ------------------------------------------------------------------

    def test_comma_separated_valid_list(self) -> None:
        """A comma-separated list of valid backends is accepted and returned unchanged."""
        result = validate_backend("text", "google,brave")
        assert result == "google,brave"

    def test_comma_separated_with_spaces(self) -> None:
        """Comma-separated list with surrounding spaces around names is accepted."""
        result = validate_backend("text", "google, brave")
        assert result == "google, brave"

    # ------------------------------------------------------------------
    # 9–10. Invalid backend raises ValueError with bad name in message
    # ------------------------------------------------------------------

    def test_invalid_backend_for_news_raises(self) -> None:
        """validate_backend('news', 'brave') raises ValueError mentioning 'brave'."""
        with pytest.raises(ValueError, match="brave"):
            validate_backend("news", "brave")

    def test_invalid_backend_for_images_raises(self) -> None:
        """validate_backend('images', 'google') raises ValueError."""
        with pytest.raises(ValueError):
            validate_backend("images", "google")

    # ------------------------------------------------------------------
    # 11. Invalid category
    # ------------------------------------------------------------------

    def test_invalid_category_raises(self) -> None:
        """An unknown category raises ValueError mentioning the category name."""
        with pytest.raises(ValueError, match="unknown"):
            validate_backend("unknown", "auto")

    def test_invalid_category_empty_string(self) -> None:
        """An empty string category raises ValueError."""
        with pytest.raises(ValueError):
            validate_backend("", "auto")

    # ------------------------------------------------------------------
    # 12. Comma-separated list with one invalid backend raises ValueError
    # ------------------------------------------------------------------

    def test_comma_separated_one_invalid_raises(self) -> None:
        """A comma-separated list where one backend is invalid raises ValueError mentioning the bad name."""
        with pytest.raises(ValueError, match="badbackend"):
            validate_backend("text", "google,badbackend")

    def test_comma_separated_first_invalid_raises(self) -> None:
        """A list where the first entry is invalid raises ValueError."""
        with pytest.raises(ValueError):
            validate_backend("news", "badone,duckduckgo")

    # ------------------------------------------------------------------
    # 13. Returns unchanged string
    # ------------------------------------------------------------------

    def test_returns_unchanged_string(self) -> None:
        """validate_backend returns the exact backend string that was passed in."""
        assert validate_backend("text", "google") == "google"

    def test_returns_unchanged_multi_string(self) -> None:
        """validate_backend returns the exact multi-backend string unchanged."""
        backend = "yahoo,duckduckgo"
        assert validate_backend("text", backend) == backend
