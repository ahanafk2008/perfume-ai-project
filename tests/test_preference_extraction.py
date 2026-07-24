"""Tests for preference extraction from natural language messages."""

from app.preferences import (
    PreferenceExtractor,
    extract_preferences_from_message,
    get_preferences,
    reset_preferences,
)


class TestPreferenceExtractor:
    def setup_method(self):
        reset_preferences()

    def test_budget_extraction(self):
        """Extract budget from price mentions."""
        result = PreferenceExtractor.extract_all("under 2000 taka")
        assert result["budget"] == 2000

    def test_no_budget(self):
        """Messages without price should not extract budget."""
        result = PreferenceExtractor.extract_all("best perfume")
        assert result["budget"] is None

    def test_gender_extraction(self):
        """Extract gender preference."""
        result = PreferenceExtractor.extract_all("men perfume")
        assert result["gender"] == "male"

        result = PreferenceExtractor.extract_all("women fragrance")
        assert result["gender"] == "female"

    def test_owned_perfumes(self):
        """Extract previously used perfumes."""
        result = PreferenceExtractor.extract_all("I already used Dior Sauvage, Bleu de Chanel")
        assert "Dior Sauvage" in result["owned_perfumes"]
        assert "Bleu de Chanel" in result["owned_perfumes"]

    def test_owned_via_have(self):
        """Extract owned perfumes from 'I have' pattern."""
        result = PreferenceExtractor.extract_all("I have CDNIM and Hawas")
        assert "CDNIM" in result["owned_perfumes"]
        assert "Hawas" in result["owned_perfumes"]

    def test_disliked_notes(self):
        """Extract disliked notes."""
        result = PreferenceExtractor.extract_all("I hate strong perfumes")
        assert "strong" in result["disliked_notes"]

    def test_disliked_via_avoid(self):
        """Extract disliked from 'avoid' pattern."""
        result = PreferenceExtractor.extract_all("avoid sweet perfumes")
        assert "sweet" in result["disliked_notes"]

    def test_style_fresh(self):
        """Extract fresh style."""
        result = PreferenceExtractor.extract_all("fresh perfume")
        assert result["style"] == "fresh"

    def test_style_elegant(self):
        """Extract elegant/luxury style."""
        result = PreferenceExtractor.extract_all("smells expensive")
        assert result["style"] == "elegant"

    def test_style_sweet(self):
        """Extract sweet style."""
        result = PreferenceExtractor.extract_all("sweet vanilla perfume")
        assert result["style"] == "sweet"

    def test_strength_light(self):
        """Extract light strength preference."""
        result = PreferenceExtractor.extract_all("not too strong")
        assert result["strength"] == "light"

    def test_strength_moderate(self):
        """Extract moderate strength."""
        result = PreferenceExtractor.extract_all("moderate projection")
        assert result["strength"] == "moderate"

    def test_longevity_high(self):
        """Extract high longevity requirement."""
        result = PreferenceExtractor.extract_all("lasts 10+ hours")
        assert result["longevity"] == "high"

    def test_longevity_via_long_lasting(self):
        """Extract longevity from 'long lasting' keyword."""
        result = PreferenceExtractor.extract_all("long lasting perfume")
        assert result["longevity"] == "high"

    def test_goals_compliments(self):
        """Extract compliments goal."""
        result = PreferenceExtractor.extract_all("gets compliments")
        assert "compliments" in result["goals"]

    def test_goals_longevity(self):
        """Extract longevity goal."""
        result = PreferenceExtractor.extract_all("needs to last all day")
        assert "compliments" in result["goals"] or "longevity" in result["goals"]

    def test_weather_hot(self):
        """Extract hot/humid weather."""
        result = PreferenceExtractor.extract_all("Bangladesh weather")
        assert result["weather"] == "hot"

    def test_weather_summer(self):
        """Extract summer weather."""
        result = PreferenceExtractor.extract_all("summer perfume")
        assert result["weather"] == "hot"

    def test_complex_message(self):
        """Extract multiple preferences from a complex message."""
        msg = (
            "I need a perfume that smells expensive, "
            "lasts 10+ hours, "
            "works in Bangladesh weather, "
            "isn't too strong, "
            "costs below 3000 BDT and gets compliments."
        )
        result = PreferenceExtractor.extract_all(msg)
        assert result["budget"] == 3000
        assert result["style"] == "elegant"
        assert result["weather"] == "hot"
        assert result["strength"] == "light"
        assert "compliments" in result["goals"]
        assert result["longevity"] == "high"

    def test_integration_with_extract_preferences(self):
        """extract_preferences_from_message should store extracted data."""
        msg = "I hate strong perfumes. Need elegant perfume under 3000."
        extract_preferences_from_message(msg, "test_user")
        prefs = get_preferences("test_user")
        assert prefs.budget == 3000
        assert prefs.style == "elegant"
        assert "strong" in prefs.disliked_notes
        assert prefs.strength_pref == "light"

    def test_owned_integration(self):
        """extract_preferences_from_message should track owned perfumes."""
        extract_preferences_from_message(
            "I already used Sauvage and CDNIM, suggest something different",
            "test_user2",
        )
        prefs = get_preferences("test_user2")
        assert "Sauvage" in prefs.owned_perfumes
        assert "CDNIM" in prefs.owned_perfumes
