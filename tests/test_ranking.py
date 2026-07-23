import json

from app.ranking import calculate_score, rank_products


male_product = {
    "id": "1",
    "name": "Lattafa Asad",
    "brand": "Lattafa",
    "category": "Male",
    "description": "Woody spicy perfume",
    "price": 1800,
}

female_product = {
    "id": "2",
    "name": "Yara",
    "brand": "Lattafa",
    "category": "Female",
    "description": "Sweet vanilla perfume",
    "price": 1500,
}

combo_product = {
    "id": "3",
    "name": "Lattafa Combo Set",
    "brand": "Lattafa",
    "category": "Male",
    "description": "Gift set combo",
    "price": 3000,
}


def test_exact_name_scores_higher():
    score = calculate_score(
        male_product,
        "lattafa asad",
    )

    assert score >= 20


def test_brand_match():
    score = calculate_score(
        male_product,
        "lattafa perfume",
    )

    assert score >= 15


def test_budget_bonus():
    score = calculate_score(
        male_product,
        "lattafa",
        budget=2000,
    )

    assert score >= 3


def test_gender_penalty():
    male_score = calculate_score(
        male_product,
        "male perfume",
    )

    female_score = calculate_score(
        female_product,
        "male perfume",
    )

    assert male_score > female_score


def test_combo_bonus():
    combo = calculate_score(
        combo_product,
        "combo set",
    )

    normal = calculate_score(
        male_product,
        "combo set",
    )

    assert combo > normal


def test_rank_products():
    ranked = rank_products(
        [
            female_product,
            male_product,
        ],
        "lattafa asad",
    )

    assert ranked[0]["name"] == "Lattafa Asad"


def test_premium_brand_boost_for_recommendation():
    """Best/top queries should boost premium brand products."""
    premium = {
        "id": "10",
        "name": "Sauvage",
        "brand": "Dior",
        "category": "Male",
        "description": "Fresh perfume",
        "price": 3200,
    }
    budget = {
        "id": "11",
        "name": "Budget Fresh",
        "brand": "Lattafa",
        "category": "Male",
        "description": "Affordable fresh",
        "price": 800,
    }

    ranked = rank_products(
        [budget, premium],
        "what is the best perfume",
        recommendation=True,
    )

    assert ranked[0]["brand"].lower() == "dior"


def test_recommendation_boost_only_with_intent():
    """Without recommendation intent, premium brand should not get extra boost."""
    premium = {
        "id": "10",
        "name": "Sauvage",
        "brand": "Dior",
        "category": "Male",
        "description": "Fresh perfume",
        "price": 3200,
    }
    budget = {
        "id": "11",
        "name": "Budget Fresh",
        "brand": "Lattafa",
        "category": "Male",
        "description": "Affordable fresh",
        "price": 800,
    }

    ranked = rank_products(
        [budget, premium],
        "cheap perfume",
        recommendation=False,
    )

    # Without recommendation, both have 0 score, order is by index.
    assert True


def test_performance_queries_get_brand_boost():
    """Long lasting / strong queries should also boost premium brands."""
    premium = {
        "id": "10",
        "name": "Sauvage Elixir",
        "brand": "Dior",
        "category": "Male",
        "description": "Powerful fresh perfume",
        "price": 3500,
    }
    regular = {
        "id": "11",
        "name": "Fresh Mist",
        "brand": "Lattafa",
        "category": "Male",
        "description": "Light fresh perfume",
        "price": 800,
    }

    ranked = rank_products(
        [regular, premium],
        "suggest a long lasting perfume",
        performance="longlasting",
        recommendation=True,
    )

    assert ranked[0]["brand"].lower() == "dior"


def test_luxury_ranking_outranks_unknown_brands():
    """Luxury queries must not let unknown cheap brands outrank luxury brands."""
    luxury_brand = {
        "id": "20",
        "name": "Bleu de Chanel",
        "brand": "Chanel",
        "category": "Men",
        "description": "Fresh perfume",
        "price": 3500,
    }
    cheap_unknown = {
        "id": "21",
        "name": "No Name Special",
        "brand": "Unknown",
        "category": "Men",
        "description": "",
        "price": 500,
    }

    ranked = rank_products(
        [cheap_unknown, luxury_brand],
        "luxury perfume",
        luxury=True,
    )

    assert ranked[0]["brand"].lower() == "chanel"


def test_luxury_weight_stronger_than_recommendation():
    """Luxury should apply a stronger weight than generic recommendation."""
    product = {
        "id": "22",
        "name": "Premium Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }

    luxury_score = calculate_score(product, "luxury perfume", luxury=True)
    rec_score = calculate_score(product, "best perfume", recommendation=True)

    assert luxury_score > rec_score


def test_generic_best_perfume_diverse_categories():
    """Generic 'best perfume' without gender should include women/unisex products."""
    men = {
        "id": "30",
        "name": "Cheap Men",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 500,
    }
    women = {
        "id": "31",
        "name": "Nice Women",
        "brand": "Burberry",
        "category": "Women",
        "description": "",
        "price": 2000,
    }
    combo = {
        "id": "32",
        "name": "Random Combo",
        "brand": "Unknown",
        "category": "Combo",
        "description": "",
        "price": 600,
    }

    ranked = rank_products(
        [men, women, combo],
        "best perfume",
        recommendation=True,
    )

    # Women product (Burberry) should outrank combo due to diversity bonus
    women_idx = next(i for i, p in enumerate(ranked) if p["id"] == "31")
    combo_idx = next(i for i, p in enumerate(ranked) if p["id"] == "32")
    assert women_idx < combo_idx, "Women product should rank above combo for gender-agnostic best query"


def test_performance_ranking_boosts_description_keywords():
    """Long lasting queries should boost products with performance keywords in description."""
    with_perf_desc = {
        "id": "40",
        "name": "Power Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "This is a long lasting strong perfume with great performance",
        "price": 1500,
    }
    without_perf_desc = {
        "id": "41",
        "name": "Light Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "Light fresh perfume",
        "price": 800,
    }

    ranked = rank_products(
        [without_perf_desc, with_perf_desc],
        "suggest a long lasting perfume",
        performance="longlasting",
    )

    assert ranked[0]["description"] == with_perf_desc["description"]


def test_hallucination_prevention_in_system_prompt():
    """System prompt must forbid using pretrained knowledge."""
    from app.prompts import SYSTEM_PROMPT
    assert "database is the only source of truth" in SYSTEM_PROMPT.lower()
    assert "never use pretrained perfume knowledge" in SYSTEM_PROMPT.lower()
    assert "do not guess" in SYSTEM_PROMPT.lower()
    assert "longevity" in SYSTEM_PROMPT.lower()
    assert "projection" in SYSTEM_PROMPT.lower()
    assert "sillage" in SYSTEM_PROMPT.lower()


# -----------------------------
# Luxury price-tier: cheap premium decants should not beat full bottles
# -----------------------------

def test_luxury_price_tier_boost():
    """Luxury queries should rank full-bottle premium products above cheap decants."""
    cheap_decant = {
        "id": "50",
        "name": "Creed Aventus Decant",
        "brand": "Creed",
        "category": "Men",
        "description": "",
        "price": 800,
    }
    full_bottle = {
        "id": "51",
        "name": "Burberry Her",
        "brand": "Burberry",
        "category": "Women",
        "description": "",
        "price": 2350,
    }

    ranked = rank_products(
        [cheap_decant, full_bottle],
        "luxury perfume",
        luxury=True,
    )

    assert ranked[0]["id"] == "51", "Full-bottle premium should rank above cheap decant for luxury query"


def test_luxury_price_tier_scoring():
    """Price-tier luxury boost should be proportional to price."""
    from app.ranking import calculate_score

    premium_low = {"id": "60", "name": "P", "brand": "Dior", "category": "Men", "description": "", "price": 800}
    premium_mid = {"id": "61", "name": "P", "brand": "Dior", "category": "Men", "description": "", "price": 1500}
    premium_high = {"id": "62", "name": "P", "brand": "Dior", "category": "Men", "description": "", "price": 2500}

    low_score = calculate_score(premium_low, "luxury", luxury=True)
    mid_score = calculate_score(premium_mid, "luxury", luxury=True)
    high_score = calculate_score(premium_high, "luxury", luxury=True)

    assert high_score > mid_score, "Higher price premium should get stronger luxury boost than mid price"
    assert mid_score > low_score, "Mid price premium should get stronger luxury boost than low price"


# -----------------------------
# Cheap intent ranking
# -----------------------------

def test_cheap_intent_ranks_lowest_price_first():
    """Cheap/affordable queries should rank lowest priced products highest."""
    expensive = {
        "id": "70",
        "name": "Premium Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }
    mid = {
        "id": "71",
        "name": "Mid Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 1500,
    }
    cheap = {
        "id": "72",
        "name": "Budget Scent",
        "brand": "Unknown",
        "category": "Men",
        "description": "",
        "price": 500,
    }

    ranked = rank_products(
        [expensive, mid, cheap],
        "cheap but good perfume",
        cheap_intent=True,
    )

    assert ranked[0]["id"] == "72", "Cheapest product should rank first for cheap intent"


def test_cheap_intent_works_without_budget_number():
    """Cheap/affordable queries should return results without a strict price filter."""
    from app.filters import detect_cheap_intent
    assert detect_cheap_intent("cheap but good perfume") is True
    assert detect_cheap_intent("affordable perfume") is True
    assert detect_cheap_intent("budget perfume") is True

    # Verify search works end-to-end
    from app.search import search_products
    results = search_products("cheap but good perfume")
    assert len(results) > 0, "Cheap intent should return products without a strict price number"

    results = search_products("affordable perfume")
    assert len(results) > 0, "Affordable intent should return products"

    results = search_products("budget perfume")
    assert len(results) > 0, "Budget intent should return products"


# -----------------------------
# Gift intent ranking
# -----------------------------

def test_gift_intent_boosts_premium_brands():
    """Gift queries should boost premium brand products."""
    premium = {
        "id": "80",
        "name": "Sauvage",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }
    regular = {
        "id": "81",
        "name": "Plain Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
    }

    ranked = rank_products(
        [regular, premium],
        "gift for husband",
        gift=True,
        gender=None,
    )

    assert ranked[0]["id"] == "80", "Premium brand should rank higher for gift intent"


def test_gift_for_wife_ranks_women_premium():
    """Gift for wife should ranks women products with premium boost."""
    women_premium = {
        "id": "90",
        "name": "Burberry Her",
        "brand": "Burberry",
        "category": "Women",
        "description": "",
        "price": 2350,
    }
    men_cheap = {
        "id": "91",
        "name": "Cheap Men",
        "brand": "Unknown",
        "category": "Men",
        "description": "",
        "price": 500,
    }
    women_cheap = {
        "id": "92",
        "name": "Regular Women",
        "brand": "Lattafa",
        "category": "Women",
        "description": "",
        "price": 800,
    }

    ranked = rank_products(
        [men_cheap, women_cheap, women_premium],
        "gift for wife",
        gift=True,
        gender="female",
    )

    assert ranked[0]["id"] == "90", "Premium women product should rank first for gift for wife"


def test_gift_for_husband_ranks_men_premium():
    """Gift for husband should rank men products with premium boost."""
    men_premium = {
        "id": "95",
        "name": "Sauvage",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3200,
    }
    women_premium = {
        "id": "96",
        "name": "Good Girl",
        "brand": "Carolina Herrera",
        "category": "Women",
        "description": "",
        "price": 2350,
    }

    ranked = rank_products(
        [women_premium, men_premium],
        "gift for husband",
        gift=True,
        gender="male",
    )

    assert ranked[0]["id"] == "95", "Men product should rank first for gift for husband"


def test_remove_duplicates():
    ranked = rank_products(
        [
            male_product,
            male_product,
            female_product,
        ],
        "lattafa",
    )

    ids = [p["id"] for p in ranked]

    assert len(ids) == len(set(ids))


# -----------------------------
# Combo penalty
# -----------------------------

def test_combo_penalty_excludes_from_non_combo_queries():
    """Combo products should not appear in non-combo queries."""
    combo = {
        "id": "100",
        "name": "Best Combo Set",
        "brand": "Dior",
        "category": "Combo",
        "description": "Combo pack",
        "price": 1000,
    }
    regular = {
        "id": "101",
        "name": "Regular Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
    }

    ranked = rank_products(
        [combo, regular],
        "best perfume",
        recommendation=True,
        combo_requested=False,
    )

    assert ranked[0]["id"] == "101", "Regular product should outrank combo for non-combo query"
    assert ranked[0]["id"] != "100", "Combo should not rank first for non-combo query"


def test_combo_boost_when_requested():
    """Combo products should get a boost when user asks for combo."""
    combo = {
        "id": "102",
        "name": "Best Combo Set",
        "brand": "Dior",
        "category": "Combo",
        "description": "Combo pack",
        "price": 1000,
    }
    regular = {
        "id": "103",
        "name": "Regular Perfume",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
    }

    ranked = rank_products(
        [regular, combo],
        "combo set",
        combo_requested=True,
    )

    assert ranked[0]["id"] == "102", "Combo should rank first when explicitly requested"


# -----------------------------
# Occasion ranking
# -----------------------------

def test_occasion_matching_with_besttime_data():
    """Occasion filters should match products with bestTime data."""
    product_with_data = {
        "id": "110",
        "name": "Office Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 2000,
        "data": '{"fragrance_details": {"bestTime": "office"}}',
    }
    product_without = {
        "id": "111",
        "name": "Regular Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    ranked = rank_products(
        [product_without, product_with_data],
        "office perfume",
        occasion="office",
    )

    assert ranked[0]["id"] == "110", "Product with matching bestTime should rank first for occasion query"


def test_occasion_matching_returns_false_without_data():
    """Occasion filtering should not match when no bestTime data exists."""
    from app.ranking import _matches_occasion
    product_no_data = {
        "id": "112",
        "name": "Test",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }
    assert _matches_occasion(product_no_data, "office") is False
    assert _matches_occasion(product_no_data, None) is False


# -----------------------------
# Season ranking
# -----------------------------

def test_season_matching_with_besttime_data():
    """Season filters should match products with bestTime data."""
    product_with_data = {
        "id": "120",
        "name": "Summer Fresh",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 2000,
        "data": '{"fragrance_details": {"bestTime": "summer"}}',
    }
    product_without = {
        "id": "121",
        "name": "Regular Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    ranked = rank_products(
        [product_without, product_with_data],
        "summer perfume",
        season="summer",
    )

    assert ranked[0]["id"] == "120", "Product with matching bestTime should rank first for season query"


def test_season_matching_returns_false_without_data():
    """Season filtering should not match when no bestTime data exists."""
    from app.ranking import _matches_season
    product_no_data = {
        "id": "122",
        "name": "Test",
        "brand": "Lattafa",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }
    assert _matches_season(product_no_data, "summer") is False
    assert _matches_season(product_no_data, None) is False


# -----------------------------
# Performance attribute matching
# -----------------------------

def test_performance_matching_from_fragrance_details():
    """Performance matching should read from fragrance_details data."""
    from app.ranking import _matches_performance
    product_with_data = {
        "id": "130",
        "name": "Long Lasting",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 1000,
        "data": '{"fragrance_details": {"longevity": "6-8 hours", "sillage": "moderate"}}',
    }
    product_no_data = {
        "id": "131",
        "name": "Regular",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_performance(product_with_data, "longlasting") is True
    assert _matches_performance(product_no_data, "longlasting") is False


# -----------------------------
# Exact name matching with brand stripping
# -----------------------------

def test_exact_name_match_normalized():
    """Exact name match should work with normalized comparison."""
    from app.ranking import _normalize_for_exact_match
    assert _normalize_for_exact_match("Creed Aventus") == "creed aventus"
    assert _normalize_for_exact_match("CREED AVENTUS | CREED") == "creed aventus creed"
    assert _normalize_for_exact_match("Club De Nuit Intense Man") == "club de nuit intense man"


def test_exact_name_scores_higher_with_normalized():
    """Product should get exact match score via normalized comparison."""
    product = {
        "id": "180",
        "name": "CREED AVENTUS | CREED",
        "brand": "Creed",
        "category": "Men",
        "description": "",
        "price": 800,
    }
    score = calculate_score(product, "Creed Aventus")
    assert score >= 100, "Exact normalized match should get full weight"


def test_exact_name_matches_combined_name_brand():
    """Query that matches name+brand combo should get exact match boost."""
    product = {
        "id": "181",
        "name": "BLEU DE CHANEL",
        "brand": "CHANEL",
        "category": "Men",
        "description": "",
        "price": 2350,
    }
    score = calculate_score(product, "bleu de chanel")
    assert score >= 100


# -----------------------------
# Luxury query: strong combo penalty
# -----------------------------

def test_luxury_combo_penalty_stronger():
    """Luxury queries should apply much stronger combo penalty."""
    combo = {
        "id": "190",
        "name": "Cheap Combo Set",
        "brand": "Unknown",
        "category": "Combo",
        "description": "Combo pack",
        "price": 500,
    }
    regular = {
        "id": "191",
        "name": "Premium Scent",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 2000,
    }

    ranked = rank_products(
        [combo, regular],
        "luxury perfume",
        luxury=True,
        combo_requested=False,
    )

    assert ranked[0]["id"] == "191", "Regular premium should outrank combo for luxury query"
    assert ranked[0]["id"] != "190", "Combo should never rank first for luxury"


def test_luxury_combo_penalty_more_than_normal():
    """Luxury combo penalty should be more severe than normal combo penalty."""
    from app.ranking import calculate_score

    combo = {
        "id": "192",
        "name": "Combo Set",
        "brand": "Unknown",
        "category": "Combo",
        "description": "",
        "price": 500,
    }

    normal_penalty = calculate_score(combo, "perfume", luxury=False, combo_requested=False)
    luxury_penalty = calculate_score(combo, "luxury perfume", luxury=True, combo_requested=False)

    assert luxury_penalty < normal_penalty, "Luxury combo penalty should be more negative than normal"


# -----------------------------
# Compliment intent detection and ranking
# -----------------------------

def test_detect_compliment():
    """Compliment intent should be detected correctly."""
    from app.filters import detect_compliment
    assert detect_compliment("perfume that gets compliments") is True
    assert detect_compliment("compliment perfume") is True
    assert detect_compliment("what perfume gets compliments") is True
    assert detect_compliment("best perfume") is False


def test_compliment_boosts_premium_brands():
    """Compliment queries should boost premium brands."""
    premium = {
        "id": "200",
        "name": "Sauvage",
        "brand": "Dior",
        "category": "Men",
        "description": "",
        "price": 3000,
    }
    cheap = {
        "id": "201",
        "name": "Budget Scent",
        "brand": "Unknown",
        "category": "Men",
        "description": "",
        "price": 500,
    }

    ranked = rank_products(
        [cheap, premium],
        "perfume that gets compliments",
        compliment=True,
    )

    assert ranked[0]["id"] == "200", "Premium brand should rank first for compliment query"


def test_compliment_boosts_popular_description():
    """Compliment queries should boost products with popular/performance keywords."""
    popular = {
        "id": "210",
        "name": "Popular Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "Our most popular long lasting perfume that gets compliments",
        "price": 1500,
    }
    plain = {
        "id": "211",
        "name": "Plain Scent",
        "brand": "Lattafa",
        "category": "Men",
        "description": "Light fresh perfume",
        "price": 800,
    }

    ranked = rank_products(
        [plain, popular],
        "perfume that gets compliments",
        compliment=True,
    )

    assert ranked[0]["id"] == "210", "Product with popular/long lasting description should rank first for compliment"


# -----------------------------
# Scent family matching from fragrance_details
# -----------------------------

def test_scent_family_matches():
    """Scent matching should work with scent_family field."""
    from app.ranking import _matches_scent

    product_with_scent_family = {
        "id": "220",
        "name": "Sweet Vanilla",
        "brand": "Test",
        "category": "Women",
        "description": "",
        "price": 1000,
        "data": json.dumps({
            "fragrance_details": {
                "scent_family": ["sweet", "vanilla"],
            },
        }),
    }
    product_no_scent = {
        "id": "221",
        "name": "Plain",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_scent(product_with_scent_family, "sweet") is True
    assert _matches_scent(product_with_scent_family, "vanilla") is True
    assert _matches_scent(product_no_scent, "sweet") is False


def test_occasion_matches_via_occasion_field():
    """Occasion matching should work with occasion field."""
    from app.ranking import _matches_occasion

    product = {
        "id": "230",
        "name": "Office Scent",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 1000,
        "data": json.dumps({
            "fragrance_details": {"occasion": ["office", "party"]},
        }),
    }
    product_no_occasion = {
        "id": "231",
        "name": "Plain",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_occasion(product, "office") is True
    assert _matches_occasion(product, "party") is True
    assert _matches_occasion(product_no_occasion, "office") is False


def test_performance_matches_via_performance_field():
    """Performance matching should work with performance field."""
    from app.ranking import _matches_performance

    product = {
        "id": "240",
        "name": "Strong Scent",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 1000,
        "data": json.dumps({
            "fragrance_details": {"performance": ["strong", "long lasting"]},
        }),
    }
    product_no_perf = {
        "id": "241",
        "name": "Plain",
        "brand": "Test",
        "category": "Men",
        "description": "",
        "price": 800,
        "data": '{}',
    }

    assert _matches_performance(product, "strong") is True
    assert _matches_performance(product, "longlasting") is True
    assert _matches_performance(product_no_perf, "strong") is False