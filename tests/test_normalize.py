from app.normalize import normalize, tokenize


def test_empty_string():
    assert normalize("") == ""


def test_lowercase():
    assert normalize("HELLO") == "hello"


def test_trim_spaces():
    assert normalize("   hello   ") == "hello"


def test_collapse_spaces():
    assert normalize("hello     world") == "hello world"


def test_remove_punctuation():
    assert normalize("hello!!!") == "hello"


def test_perfume_typo():
    assert normalize("perfum") == "perfume"


def test_perfumes_plural():
    assert normalize("perfumes") == "perfume"


def test_female_words():
    assert normalize("girls") == "female"
    assert normalize("women") == "female"
    assert normalize("wife") == "female"


def test_male_words():
    assert normalize("boys") == "male"
    assert normalize("gentlemen") == "male"
    assert normalize("husband") == "male"


def test_banglish():
    assert normalize("cheleder perfume") == "male perfume"
    assert normalize("meyeder perfume") == "female perfume"


def test_bangla_words():
    assert normalize("পারফিউম") == "perfume"
    assert normalize("সুগন্ধি") == "perfume"
    assert normalize("আতর") == "attar"


def test_possessives():
    assert normalize("men's perfume") == "male perfume"
    assert normalize("women's perfume") == "female perfume"


def test_tokenize():
    assert tokenize("Girls perfumes") == ["female", "perfume"]


def test_none_punctuation_only():
    assert normalize("!!!") == ""


def test_ml_not_changed():
    assert normalize("100 ml") == "100 ml"


def test_common_abbreviation():
    assert normalize("100 mls") == "100 ml"


def test_case_and_typo():
    assert normalize("PeRfUmEe") == "perfume"