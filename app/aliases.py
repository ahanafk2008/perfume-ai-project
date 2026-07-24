"""Common perfume name aliases database.

Maps shorthand names, acronyms, and common misspellings
to canonical product names for search resolution.
"""

PERFUME_ALIASES: dict[str, str] = {
    # CDNIM / Armaf
    "cdnim": "CLUB DE NUIT INSTENSE MAN",
    "club de nuit": "CLUB DE NUIT INSTENSE MAN",
    "club de nuit intense": "CLUB DE NUIT INSTENSE MAN",
    "club de nuit intense man": "CLUB DE NUIT INSTENSE MAN",
    "cdn": "CLUB DE NUIT INSTENSE MAN",
    "cdnim man": "CLUB DE NUIT INSTENSE MAN",
    "armaf cdnim": "CLUB DE NUIT INSTENSE MAN",

    # Bleu de Chanel
    "bdc": "BLEU DE CHANEL",
    "bleu de chanel": "BLEU DE CHANEL",
    "bleu": "BLEU DE CHANEL",
    "chanel bleu": "BLEU DE CHANEL",

    # YSL Y
    "ysl y": "YSL Y",
    "y ysl": "YSL Y",
    "y eau de parfum": "YSL Y",
    "ysl y edp": "YSL Y",

    # Stronger With You
    "swy": "STRONGER WITH YOU",
    "stronger with you": "STRONGER WITH YOU",
    "armani stronger with you": "STRONGER WITH YOU",

    # Afnan 9PM
    "9pm": "AFNAN 9 PM ELIXIR",
    "9 pm": "AFNAN 9 PM ELIXIR",
    "afnan 9pm": "AFNAN 9 PM ELIXIR",
    "afnan 9 pm": "AFNAN 9 PM ELIXIR",
    "afnan nine pm": "AFNAN 9 PM ELIXIR",

    # Lattafa Asad
    "asad": "LATTAFA ASAD",
    "lattafa asad": "LATTAFA ASAD",

    # Lattafa Khamra / Khamrah
    "khamra": "LATTAFA KHAMRAH",
    "khamrah": "LATTAFA KHAMRAH",
    "lattafa khamra": "LATTAFA KHAMRAH",
    "lattafa khamrah": "LATTAFA KHAMRAH",

    # Lattafa Yara
    "yara": "LATTAFA YARA",
    "lattafa yara": "LATTAFA YARA",

    # Hawas
    "hawas": "RASASI HAWAS",
    "rasasi hawas": "RASASI HAWAS",
    "rasasi": "RASASI HAWAS",

    # Qahwa (commonly Lattafa Qahwa or similar)
    "qahwa": "LATTAFA KHAMRAH",
    "qahwah": "LATTAFA KHAMRAH",

    # Creed Aventus
    "aventus": "CREED AVENTUS",
    "creed aventus": "CREED AVENTUS",

    # Dior Sauvage
    "sauvage": "DIOR SAUVAGE",
    "dior sauvage": "DIOR SAUVAGE",

    # Dior
    "miss dior": "MISS DIOR",
    "dior miss": "MISS DIOR",

    # Acqua di Gio
    "adg": "ACQUA DI GIO",
    "acqua di gio": "ACQUA DI GIO",
    "armani acqua di gio": "ACQUA DI GIO",

    # CK One
    "ck one": "CK ONE",
    "ck": "CK ONE",
    "calvin klein one": "CK ONE",

    # Versace Eros
    "eros": "VERSACE EROS",
    "versace eros": "VERSACE EROS",

    # LV Imagination
    "lv imagination": "LV IMAGINATION",
    "imagination": "LV IMAGINATION",
    "louis vuitton imagination": "LV IMAGINATION",

    # Tobacco Vanille
    "tobacco vanille": "TOBACCO VANILLE",
    "tom ford tobacco vanille": "TOBACCO VANILLE",

    # Burberry Her
    "burberry her": "BURBERRY HER",

    # Good Girl
    "good girl": "GOOD GIRL",
    "carolina herrera good girl": "GOOD GIRL",

    # Black Opium
    "black opium": "BLACK OPIUM",
    "ysl black opium": "BLACK OPIUM",

    # Ultra Male
    "ultra male": "ULTRA MALE",
    "jpg ultra male": "ULTRA MALE",
    "jean paul gaultier ultra male": "ULTRA MALE",

    # Cool Water
    "cool water": "COOL WATER",
    "davidoff cool water": "COOL WATER",

    # Nautica Voyage
    "nautica voyage": "NAUTICA VOYAGE",
    "voyage": "NAUTICA VOYAGE",

    # Salvo Intense
    "salvo": "SALVO INTENSE",
    "salvo intense": "SALVO INTENSE",

    # Bacarrat Rouge 540
    "br540": "BACCARAT ROUGE 540",
    "baccarat rouge": "BACCARAT ROUGE 540",
    "baccarat": "BACCARAT ROUGE 540",

    # Vampire Blood
    "vampire blood": "VAMPIRE BLOOD",
}

# Mapping of intent ranking keywords to comparison scoring criteria
RANKING_INTENTS: dict[str, str] = {
    "strongest": "longevity",
    "richest": "richness",
    "most luxurious": "luxury",
    "most compliments": "compliments",
    "best blind buy": "blind_buy",
    "worth buying": "value",
    "projects most": "projection",
    "projects more": "projection",
    "lasts longer": "longevity",
    "longest lasting": "longevity",
    "best projection": "projection",
    "most versatile": "versatility",
    "best value": "value",
    "pick one": "overall",
    "pick the best": "overall",
    "which is better": "overall",
    "which one is better": "overall",
    "choose one": "overall",
    "recommend one": "overall",
}


def resolve_alias(name: str) -> str:
    """Resolve a perfume alias to its canonical name.

    Returns the original name if no alias matches.
    """
    key = name.strip().lower()
    if key in PERFUME_ALIASES:
        return PERFUME_ALIASES[key]

    for alias, canonical in PERFUME_ALIASES.items():
        if alias in key or key in alias:
            return canonical

    return name


def get_ranking_criteria(query: str) -> str | None:
    """Detect if the query matches a ranking intent and return the criteria key."""
    q = query.lower().strip()
    for phrase, criteria in RANKING_INTENTS.items():
        if phrase in q:
            return criteria
    return None