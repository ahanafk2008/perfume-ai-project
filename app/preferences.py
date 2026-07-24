"""User preference memory system.

Tracks per-user preferences during conversation and uses them
automatically in future recommendations.
"""

import logging
import re
from collections import defaultdict
from typing import Any, ClassVar

from app.filters import (
    detect_gender,
    detect_occasion,
    detect_season,
    extract_budget,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "cli"


class PreferenceExtractor:
    """Extracts structured preferences from natural language messages."""

    STRENGTH_KEYWORDS: ClassVar[dict[str, set[str]]] = {
        "light": {"light", "soft", "gentle", "subtle", "mild", "weak", "not strong", "not too strong", "not overpowering", "not heavy", "not intense"},
        "moderate": {"moderate", "medium", "balanced", "versatile", "medium projection"},
        "strong": {"strong", "powerful", "intense", "beast", "beastmode", "heavy", "loud"},
    }

    GOAL_KEYWORDS: ClassVar[dict[str, set[str]]] = {
        "compliments": {"compliment", "compliments", "attention", "notice", "praise", "attract", "magnetic"},
        "longevity": {"long lasting", "last long", "lasts long", "longevity", "all day", "whole day"},
        "projection": {"projection", "sillage", "beast mode", "beastmode", "strong projection"},
        "office_safe": {"office", "professional", "work", "corporate", "formal"},
        "date": {"date", "romantic", "dinner", "night out"},
    }

    WEATHER_KEYWORDS: ClassVar[dict[str, set[str]]] = {
        "hot": {"hot", "heat", "humid", "bangladesh", "dhaka", "summer", "warm"},
        "cold": {"cold", "winter", "chilly", "cool"},
        "rainy": {"rainy", "monsoon", "rain", "wet"},
    }

    OWNED_PATTERNS: ClassVar[list[re.Pattern]] = [
        re.compile(r"(?:i\s+(?:have|own|already\s+(?:have|use|own))\s+)(.+?)(?:\.|$)", re.IGNORECASE),
        re.compile(r"(?:i\s+used\s+)(.+?)(?:\.|$)", re.IGNORECASE),
        re.compile(r"(?:already\s+(?:used|have|own|finished)\s+)(.+?)(?:\.|$)", re.IGNORECASE),
        re.compile(r"(?:i\s+use\s+)(.+?)(?:\.|$)", re.IGNORECASE),
    ]

    DISLIKE_PATTERNS: ClassVar[list[re.Pattern]] = [
        re.compile(r"(?:i\s+(?:don't like|hate|dislike|avoid|don't want)\s+)(.+?)(?:\.|,|$)", re.IGNORECASE),
        re.compile(r"(?:hate|avoid)\s+(.+?)(?:perfume|fragrance|scent|\.|,|$)", re.IGNORECASE),
        re.compile(r"(?:not\s+(?:a\s+)?fan\s+of\s+)(.+?)(?:\.|,|$)", re.IGNORECASE),
    ]

    @classmethod
    def extract_owned(cls, message: str) -> list[str]:
        """Extract perfume names the user says they already own."""
        owned = []
        for pat in cls.OWNED_PATTERNS:
            m = pat.search(message)
            if m:
                items = re.split(r"\s+(?:and|,)\s+|,\s*", m.group(1).strip())
                for item in items:
                    item = item.strip().strip(".,!?")
                    if item and len(item) > 2 and item not in owned:
                        owned.append(item)
        return owned

    @classmethod
    def extract_disliked(cls, message: str) -> list[str]:
        """Extract notes/perfumes the user dislikes."""
        disliked = []
        for pat in cls.DISLIKE_PATTERNS:
            m = pat.search(message)
            if m:
                items = re.split(r"\s+(?:and|,)\s+|,\s*", m.group(1).strip())
                for item in items:
                    item = item.strip().strip(".,!?")
                    if item and len(item) > 2 and item not in disliked:
                        disliked.append(item)
        return disliked

    @classmethod
    def extract_strength(cls, message: str) -> str | None:
        """Detect preferred strength (strong/moderate/light).

        Handles negation: 'hate strong' -> light, 'want strong' -> strong.
        """
        q = message.lower()
        # Check for negation before strength keywords
        negation_prefix = r"(?:hate|don't like|dislike|avoid|not\s+(?:a\s+)?fan|isn'?t(?:\s+too)?|not\s+(?:too\s+)?|don't\s+(?:like|want|need))"
        for strength, keywords in cls.STRENGTH_KEYWORDS.items():
            for kw in keywords:
                if kw not in q:
                    continue
                # Check if keyword is negated
                idx = q.find(kw)
                prefix = q[max(0, idx - 20):idx].strip()
                if re.search(negation_prefix, prefix):
                    # Negated -> return the OPPOSITE strength
                    if strength == "strong":
                        return "light"
                    if strength == "light":
                        return "strong"
                    return None
                return strength
        return None

    @classmethod
    def extract_goals(cls, message: str) -> list[str]:
        """Extract user goals (compliments, longevity, etc.)."""
        q = message.lower()
        goals = []
        for goal, keywords in cls.GOAL_KEYWORDS.items():
            if any(kw in q for kw in keywords) and goal not in goals:
                goals.append(goal)
        return goals

    @classmethod
    def extract_style(cls, message: str) -> str | None:
        """Extract scent style from message keywords."""
        q = message.lower()
        style_map = {
            "fresh": {"fresh", "clean", "aquatic", "citrus", "marine", "ocean"},
            "sweet": {"sweet", "vanilla", "gourmand", "candy", "sugary"},
            "woody": {"woody", "wood", "earthy", "oud", "musk"},
            "floral": {"floral", "flower", "rose", "jasmine"},
            "spicy": {"spicy", "pepper", "warm", "cinnamon"},
            "elegant": {"elegant", "sophisticated", "classy", "refined", "premium", "luxury", "expensive"},
            "powdery": {"powdery", "iris", "violet"},
        }
        for style, keywords in style_map.items():
            if any(kw in q for kw in keywords):
                return style
        return None

    @classmethod
    def extract_budget(cls, message: str) -> int | None:
        """Extract budget from message."""
        return extract_budget(message)

    @classmethod
    def extract_gender(cls, message: str) -> str | None:
        """Extract gender preference."""
        return detect_gender(message)

    @classmethod
    def extract_occasion(cls, message: str) -> str | None:
        """Extract occasion."""
        return detect_occasion(message)

    @classmethod
    def extract_season(cls, message: str) -> str | None:
        """Extract season."""
        return detect_season(message)

    @classmethod
    def extract_weather(cls, message: str) -> str | None:
        """Extract weather/climate context."""
        q = message.lower()
        for weather, keywords in cls.WEATHER_KEYWORDS.items():
            if any(kw in q for kw in keywords):
                return weather
        return None

    @classmethod
    def extract_longevity(cls, message: str) -> str | None:
        """Extract longevity requirement."""
        q = message.lower()
        if re.search(r"(10\+|10\s*hours|all\s*day|long\s*lasting|very\s*long)", q):
            return "high"
        if re.search(r"(6\+|6-8|moderate|medium|few\s*hours)", q):
            return "medium"
        if re.search(r"(short|don't\s*care|doesn't\s*matter)", q):
            return "low"
        if re.search(r"(long.?lasting|long.?evity|last\s+long|stays\s+long)", q):
            return "high"
        return None

    @classmethod
    def extract_all(cls, message: str) -> dict[str, Any]:
        """Extract all preferences from a message."""
        return {
            "owned_perfumes": cls.extract_owned(message),
            "disliked_notes": cls.extract_disliked(message),
            "budget": cls.extract_budget(message),
            "gender": cls.extract_gender(message),
            "occasion": cls.extract_occasion(message),
            "season": cls.extract_season(message),
            "style": cls.extract_style(message),
            "strength": cls.extract_strength(message),
            "longevity": cls.extract_longevity(message),
            "weather": cls.extract_weather(message),
            "goals": cls.extract_goals(message),
        }


class UserPreferences:
    """Structured user preference data."""

    def __init__(self) -> None:
        self.owned_perfumes: list[str] = []
        self.liked_notes: list[str] = []
        self.disliked_notes: list[str] = []
        self.disliked_perfumes: list[str] = []
        self.preferred_brands: list[str] = []
        self.disliked_brands: list[str] = []
        self.budget: int | None = None
        self.occasion: str | None = None
        self.weather: str | None = None
        self.projection_pref: str | None = None
        self.longevity_pref: str | None = None
        self.gender: str | None = None
        self.style: str | None = None
        self.strength_pref: str | None = None
        self.goals: list[str] | None = None
        self.authenticity_pref: str | None = None
        self.clone_pref: str | None = None
        self.combo_pref: str | None = None
        self.beginner_mode: bool = False
        self.blind_buy_mode: bool = False
        self.language: str | None = None
        self.recommended_product_ids: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "owned_perfumes": self.owned_perfumes,
            "liked_notes": self.liked_notes,
            "disliked_notes": self.disliked_notes,
            "disliked_perfumes": self.disliked_perfumes,
            "preferred_brands": self.preferred_brands,
            "disliked_brands": self.disliked_brands,
            "budget": self.budget,
            "occasion": self.occasion,
            "weather": self.weather,
            "projection_pref": self.projection_pref,
            "longevity_pref": self.longevity_pref,
            "gender": self.gender,
            "style": self.style,
            "strength_pref": self.strength_pref,
            "goals": self.goals,
            "authenticity_pref": self.authenticity_pref,
            "clone_pref": self.clone_pref,
            "combo_pref": self.combo_pref,
            "beginner_mode": self.beginner_mode,
            "blind_buy_mode": self.blind_buy_mode,
            "language": self.language,
            "recommended_product_ids": self.recommended_product_ids,
        }

    def has_any_preference(self) -> bool:
        return any([
            self.owned_perfumes,
            self.liked_notes,
            self.disliked_notes,
            self.disliked_perfumes,
            self.preferred_brands,
            self.disliked_brands,
            self.budget is not None,
            self.occasion,
            self.weather,
            self.projection_pref,
            self.longevity_pref,
            self.gender,
            self.style,
            self.strength_pref,
            self.goals,
            self.authenticity_pref is not None,
            self.clone_pref is not None,
            self.combo_pref is not None,
        ])

    def format_for_prompt(self) -> str:
        parts = []
        if self.owned_perfumes:
            parts.append(f"Owns: {', '.join(self.owned_perfumes)}")
        if self.liked_notes:
            parts.append(f"Likes notes: {', '.join(self.liked_notes)}")
        if self.disliked_notes:
            parts.append(f"Dislikes notes: {', '.join(self.disliked_notes)}")
        if self.disliked_perfumes:
            parts.append(f"Avoid perfumes like: {', '.join(self.disliked_perfumes)}")
        if self.preferred_brands:
            parts.append(f"Preferred brands: {', '.join(self.preferred_brands)}")
        if self.disliked_brands:
            parts.append(f"Disliked brands: {', '.join(self.disliked_brands)}")
        if self.budget is not None:
            parts.append(f"Budget: ৳{self.budget}")
        if self.occasion:
            parts.append(f"Occasion: {self.occasion}")
        if self.weather:
            parts.append(f"Weather: {self.weather}")
        if self.projection_pref:
            parts.append(f"Projection: {self.projection_pref}")
        if self.longevity_pref:
            parts.append(f"Longevity: {self.longevity_pref}")
        if self.gender:
            parts.append(f"Gender: {self.gender}")
        if self.style:
            parts.append(f"Style: {self.style}")
        if self.strength_pref:
            parts.append(f"Strength: {self.strength_pref}")
        if self.goals:
            parts.append(f"Goals: {', '.join(self.goals)}")
        if self.authenticity_pref:
            parts.append(f"Authenticity: {self.authenticity_pref}")
        if self.clone_pref:
            parts.append(f"Clone preference: {self.clone_pref}")
        if self.combo_pref:
            parts.append(f"Combo preference: {self.combo_pref}")
        if self.beginner_mode:
            parts.append("Mode: beginner (explain scent families)")
        if self.blind_buy_mode:
            parts.append("Mode: blind-buy (prefer versatile mass-appealing)")
        formatted = "; ".join(parts)
        return formatted if formatted else "None yet"


_user_preferences: dict[str, UserPreferences] = defaultdict(UserPreferences)


def get_preferences(user_id: str = DEFAULT_USER_ID) -> UserPreferences:
    return _user_preferences[user_id]


def extract_preferences_from_message(
    message: str,
    user_id: str = DEFAULT_USER_ID,
) -> dict[str, Any]:
    """Parse a user message and extract/update preference information.

    Returns a dict of preference fields that were updated.
    """
    prefs = _user_preferences[user_id]
    q = message.lower().strip()
    updated: dict[str, Any] = {}

    # Detect beginner mode
    if re.search(r"(know nothing|don't know|new to|beginner|just started|no idea|knew na|kisu jani na)", q) and not prefs.beginner_mode:
        prefs.beginner_mode = True
        updated["beginner_mode"] = True

    # Detect blind-buy mode
    if re.search(r"(blind.?buy|can't smell|without smelling|not testing|blind order)", q) and not prefs.blind_buy_mode:
            prefs.blind_buy_mode = True
            updated["blind_buy_mode"] = True

    # Use PreferenceExtractor for richer extraction
    extracted = PreferenceExtractor.extract_all(message)

    # Merge owned perfumes
    for item in extracted.get("owned_perfumes", []):
        if item and item not in prefs.owned_perfumes:
            prefs.owned_perfumes.append(item)
            updated.setdefault("owned_perfumes", []).append(item)

    # Merge disliked notes/perfumes
    for item in extracted.get("disliked_notes", []):
        if item and item not in prefs.disliked_notes:
            prefs.disliked_notes.append(item)
            updated.setdefault("disliked_notes", []).append(item)

    # Detect liked notes
    like_patterns = [
        r"(?:i\s+(?:like|love|enjoy|prefer)\s+)(.+?)(?:notes|scent|smell|fragrance|\.|,|$)",
        r"(?:like|love|prefer)\s+(.+?)(?:notes|scent|\.|,|$)",
        r"(?:pasand\s+)\s*(.+?)(?:\.|,|$)",
        r"(?:pachondo\s+)\s*(.+?)(?:\.|,|$)",
    ]
    for pat in like_patterns:
        m = re.search(pat, q)
        if m:
            likes = m.group(1).strip()
            for item in re.split(r"\s+(?:and|,)\s+", likes):
                item = item.strip()
                if item and item not in prefs.liked_notes:
                    prefs.liked_notes.append(item)
                    updated.setdefault("liked_notes", []).append(item)

    # Update budget if found
    budget = extracted.get("budget")
    if budget is not None:
        prefs.budget = budget
        updated["budget"] = budget

    # Update gender preference
    gender = extracted.get("gender")
    if gender:
        prefs.gender = gender
        updated["gender"] = gender

    # Update occasion
    occasion = extracted.get("occasion")
    if occasion:
        prefs.occasion = occasion
        updated["occasion"] = occasion

    # Update season/weather
    weather = extracted.get("weather")
    if weather and prefs.weather != weather:
        prefs.weather = weather
        updated["weather"] = weather

    season = extracted.get("season")
    if season and prefs.weather != season:
        prefs.weather = season
        updated["weather"] = season

    # Update style preference
    style = extracted.get("style")
    if style:
        prefs.style = style
        updated["style"] = style

    # Update strength preference
    strength = extracted.get("strength")
    if strength:
        prefs.strength_pref = strength
        updated["strength_pref"] = strength

    # Update longevity preference
    longevity = extracted.get("longevity")
    if longevity:
        if longevity == "high" and prefs.longevity_pref != "long":
            prefs.longevity_pref = "long"
            updated["longevity_pref"] = "long"
    elif re.search(r"(?:long.?lasting|long.?evity|last\s+long|lasts\s+long|stays\s+long)", q) and prefs.longevity_pref != "long":
        prefs.longevity_pref = "long"
        updated["longevity_pref"] = "long"

    # Detect projection preference
    if re.search(r"(?:strong\s+projection|beast.?mode|good\s+projection|high\s+sillage)", q) and prefs.projection_pref != "strong":
            prefs.projection_pref = "strong"
            updated["projection_pref"] = "strong"

    # Detect preferred brands ("I like Dior", "I love Lattafa")
    brand_like_patterns = [
        r"(?:i\s+(?:like|love|prefer|enjoy)\s+)(?:the\s+)?(?:brand\s+)?(.+?)(?:\s+perfume|\s+fragrance|\.|,|$)",
        r"(?:i\s+(?:like|love|prefer)\s+)(.+?)(?:\s+brand|\s+perfumes|\s+fragrances|\.|,|$)",
    ]
    for pat in brand_like_patterns:
        m = re.search(pat, q)
        if m:
            brand = m.group(1).strip().lower()
            for b in re.split(r"\s+(?:and|,)\s+", brand):
                b = b.strip()
                if b and b not in prefs.preferred_brands and b not in ("perfume", "fragrance"):
                    prefs.preferred_brands.append(b)
                    updated.setdefault("preferred_brands", []).append(b)

    # Detect disliked brands ("I hate Dior", "avoid CHANEL")
    brand_dislike_patterns = [
        r"(?:i\s+(?:don't like|hate|dislike|avoid)\s+)(?:the\s+)?(?:brand\s+)?(.+?)(?:\s+perfume|\s+fragrance|\.|,|$)",
        r"(?:hate|avoid|dislike)\s+(.+?)(?:\s+brand|\s+perfumes?|\s+fragrances?|\.|,|$)",
    ]
    for pat in brand_dislike_patterns:
        m = re.search(pat, q)
        if m:
            brand = m.group(1).strip().lower()
            for b in re.split(r"\s+(?:and|,)\s+", brand):
                b = b.strip()
                if b and b not in prefs.disliked_brands and b not in ("perfume", "fragrance"):
                    prefs.disliked_brands.append(b)
                    updated.setdefault("disliked_brands", []).append(b)

    # Detect authenticity preference ("only original", "show authentic", "no clones", "only inspired")
    if (re.search(r"(?:only|show|want)\s+(?:original|authentic|real)", q) or re.search(r"(?:is\s+it\s+original|is\s+this\s+authentic)", q)) and prefs.authenticity_pref != "original":
        prefs.authenticity_pref = "original"
        updated["authenticity_pref"] = "original"

    if re.search(r"(?:only|show|want)\s+inspired|no\s+(?:original|authentic)", q) and prefs.authenticity_pref != "inspired":
        prefs.authenticity_pref = "inspired"
        updated["authenticity_pref"] = "inspired"

    # Detect clone/original preference
    if re.search(r"(?:no|avoid|don't want|hate)\s+(?:clone|clones|dupe|dupes|inspired|fake|copy)", q) and prefs.clone_pref != "original_only":
        prefs.clone_pref = "original_only"
        updated["clone_pref"] = "original_only"

    if re.search(r"(?:only|show|want|prefer)\s+(?:clone|clones|dupe|dupes|inspired)", q) and prefs.clone_pref != "clone_only":
        prefs.clone_pref = "clone_only"
        updated["clone_pref"] = "clone_only"

    # Detect combo/discovery preference
    if re.search(r"(?:want|need|looking for|show|prefer)\s+(?:combo|combos|set|gift set|bundle|pack)", q) and prefs.combo_pref != "combo":
        prefs.combo_pref = "combo"
        updated["combo_pref"] = "combo"

    if re.search(r"(?:want|need|looking for|show|prefer)\s+(?:discovery|sample|sampler|tester)", q) and prefs.combo_pref != "discovery":
        prefs.combo_pref = "discovery"
        updated["combo_pref"] = "discovery"

    if re.search(r"(?:no|avoid|don't want|hate)\s+(?:combo|combos|set|gift set|bundle|pack)", q) and prefs.combo_pref != "no_combo":
        prefs.combo_pref = "no_combo"
        updated["combo_pref"] = "no_combo"

    # Update goals
    goals = extracted.get("goals", [])
    if goals:
        prefs.goals = goals
        updated["goals"] = goals

    return updated


def add_recommended_product(product_id: str, user_id: str = DEFAULT_USER_ID) -> None:
    prefs = _user_preferences[user_id]
    if product_id not in prefs.recommended_product_ids:
        prefs.recommended_product_ids.append(product_id)


def is_already_recommended(product_id: str, user_id: str = DEFAULT_USER_ID) -> bool:
    prefs = _user_preferences[user_id]
    return product_id in prefs.recommended_product_ids


def _normalize_product_name(name: str) -> str:
    """Normalize product name for matching: lowercase, strip, remove punctuation."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    return name.strip()


def _resolve_aliases(name: str) -> list[str]:
    """Resolve a product name through aliases to find all canonical forms."""
    from app.aliases import PERFUME_ALIASES
    results = [name]
    key = name.lower().strip()
    for alias, canonical in PERFUME_ALIASES.items():
        if alias in key or key in alias:
            results.append(canonical.lower().strip())
            results.append(alias)
    return list(set(results))


def _get_clone_brands() -> set[str]:
    """Return set of known clone/inspired-by brand markers."""
    return {
        "armaf", "lattafa", "rasasi", "afnan", "fragrance world",
        "maison alhambra", "pendora scents", "ard al zaafaran",
        "al haramain", "ajmal",
    }


def is_owned(product_name: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Check if a product is owned by the user. Uses alias resolution and fuzzy matching."""
    prefs = _user_preferences[user_id]
    if not prefs.owned_perfumes:
        return False

    product_norm = _normalize_product_name(product_name)
    owned_normalized = [_normalize_product_name(o) for o in prefs.owned_perfumes]

    # Direct match
    if product_norm in owned_normalized:
        return True

    # Substring match (e.g., "Sauvage" in "Dior Sauvage")
    for owned in owned_normalized:
        if owned in product_norm or product_norm in owned:
            return True

    # Alias resolution: check if product matches any alias of owned perfumes
    for owned_raw in prefs.owned_perfumes:
        owned_aliases = _resolve_aliases(owned_raw)
        for alias in owned_aliases:
            if alias and (alias in product_norm or product_norm in alias):
                return True

    # Clone detection: if owned perfume is a well-known designer/niche,
    # and product is from a clone brand with similar name
    for owned_raw in prefs.owned_perfumes:
        owned_lower = owned_raw.lower().strip()
        # Extract key words from owned perfume (e.g., "Sauvage" from "Dior Sauvage")
        owned_words = set(re.findall(r"[a-z]+", owned_lower))
        product_words = set(re.findall(r"[a-z]+", product_norm))
        shared = owned_words & product_words
        if len(shared) >= 1:
            # Check if product is from a clone brand
            for brand in _get_clone_brands():
                if brand in product_norm:
                    return True
            # Also check if owned is a well-known designer and product shares key words
            _designer_brands = {"dior", "chanel", "versace", "armani", "creed", "ysl", "prada", "gucci", "tom ford"}
            if any(db in owned_lower for db in _designer_brands) and shared:
                # Strong likelihood of clone/inspired-by
                return True

    return False


def reset_preferences(user_id: str = DEFAULT_USER_ID) -> None:
    _user_preferences[user_id] = UserPreferences()
    logger.debug("Reset preferences for user_id=%s", user_id)
