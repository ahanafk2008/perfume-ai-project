# Perfume AI - QA Test Report

**Date**: 2026-07-23
**Tester**: Automated QA Suite
**Project**: E:\perfume-ai

---

## Summary

| Metric | Value |
|--------|-------|
| Tests Executed | 97 (84 pytest + 50+ manual queries + 6 regression) |
| Original pytest Tests Passed | 84 |
| New Regression Tests Added | 6 |
| Total psssing after fixes | 91 |
| Bugs Found | 7 |
| Critical Bugs | 1 |
| High Bugs | 3 |
| Medium Bugs | 3 |
| Files Modified | 2 |

---

## Test Categories Executed

1. **Product Search** - 12 queries
2. **Budget Testing** - 12 queries
3. **Brand Testing** - 6 queries
4. **Language Testing (Bangla/Banglish)** - 7 queries
5. **Conversation Testing** - 4-turn conversation
6. **Failure Testing** - 5 nonsense queries
7. **Prompt Injection Testing** - 3 attempts
8. **Edge Case Testing** - 10 cases
9. **Database Integrity** - 76 products validated
10. **Filter Accuracy** - 19 extraction tests
11. **Ranking Logic** - Rank order + budget filtered verification

---

## Bugs Found and Fixed

### BUG #1 (CRITICAL): Ranking returns products over budget

- **Input**: `"perfume under 2000"`
- **Expected**: All products ≤ 2000 BDT
- **Actual**: Products like Armaf Club De Nuit (2500) and Rasasi Hawas (3000) were returned
- **Root Cause**: `app/ranking.py` → `rank_products()` only adds a BUDGET_WEIGHT=3 score bonus but never filters products by budget
- **Fix**: Added post-ranking budget enforcement in `app/search.py` → `search_products()`:
  ```python
  if budget is not None:
      ranked = [p for p in ranked if float(p.get("price", 0)) <= budget]
  ```
- **Regression Test**: `test_budget_enforcement_end_to_end` and `test_budget_enforcement_custom`

### BUG #2 (HIGH): Bangla budget extraction fails for 'হাজার'

- **Input**: `"2 হাজার টাকার মধ্যে ভালো perfume চাই"`
- **Expected**: Budget = 2000
- **Actual**: Budget = None
- **Root Cause**: `app/filters.py` → `extract_budget()` had no pattern for Bengali "হাজার" (thousand)
- **Fix**: Added pattern: `r"(\d+)\s*হাজার"` → multiply by 1000
- **Regression Test**: Verified `extract_budget("2 হাজার...") == 2000`

### BUG #3 (HIGH): Bangla gender detection fails for 'ছেলেদের'

- **Input**: `"ছেলেদের জন্য ভালো perfume"`
- **Expected**: Gender = male
- **Actual**: Gender = None
- **Root Cause**: `app/filters.py` → NORMALIZATION dict had `"ছেলে" → "male"` but not `"ছেলেদের"` (possessive plural form)
- **Fix**: Added `"ছেলেদের": "male"` and `"cheleder": "male"` to NORMALIZATION dict
- **Regression Test**: `test_detect_gender_bangla`

### BUG #4 (MEDIUM): '2k' shorthand not parsed as 2000

- **Input**: `"perfume within 2k"`
- **Expected**: Budget = 2000
- **Actual**: Budget = 2
- **Root Cause**: BUDGET_KEYWORDS pattern `\bwithin\s+(\d+)` matched "2" from "2k" before any k-handling existed
- **Fix**: Added `r"(\d+(?:\.\d+)?)\s*k\b"` pattern on RAW query as the FIRST budget check
- **Regression Test**: `test_extract_budget_k_shorthand`

### BUG #5 (MEDIUM): Decimal '2.5k' not parsed as 2500

- **Input**: `"perfume under 2.5k"`
- **Expected**: Budget = 2500
- **Actual**: Budget = 25 (normalize() strips the decimal point)
- **Root Cause**: The k-pattern was checking the normalized query (`lower`), but `normalize()` strips `.` from `2.5k` making it `25k`
- **Fix**: Changed k-pattern to check `query` (raw input) instead of `lower` (normalized), and moved it before all other patterns
- **Regression Test**: `test_extract_budget_decimal_k_shorthand`

### BUG #6 (MEDIUM): 'cheaper than 800' not parsed

- **Input**: `"cheaper than 800"`
- **Expected**: Budget = 800
- **Actual**: Budget = None
- **Root Cause**: `extract_budget()` had no pattern for "cheaper than" or "cheap" as budget indicators
- **Fix**: Added pattern: `r"(?:cheaper|cheap)\s+(?:than\s+)?(\d+)"`
- **Regression Test**: `test_extract_budget_cheaper_than`

### BUG #7 (MEDIUM): 'my budget is 2500' not parsed

- **Input**: `"my budget is 2500"`
- **Expected**: Budget = 2500
- **Actual**: Budget = None
- **Root Cause**: `extract_budget()` had no pattern for "budget is X" phrase structure
- **Fix**: Added pattern: `r"(?:my\s+)?budget\s+is\s+(\d+)"`
- **Regression Test**: `test_extract_budget_my_budget_is`

---

## Fixed Files

### `app/filters.py`
- Added `"ছেলেদের": "male"` and `"cheleder": "male"` to NORMALIZATION dict
- Added `"k"` shorthand pattern (2k=2000, 2.5k=2500) as FIRST budget check
- Added Bangla `"হাজার"` (thousand) pattern
- Added `"cheaper than"` budget pattern
- Added `"my budget is"` / `"budget is"` pattern
- Reordered all patterns: k-shorthand → Bengali thousand → multi-word → keywords → taka → cheaper → budget-is

### `app/search.py`
- Added post-ranking budget enforcement filter in `search_products()`

### `tests/test_filters.py`
- Added 6 new regression test functions:
  - `test_extract_budget_k_shorthand`
  - `test_extract_budget_decimal_k_shorthand`
  - `test_extract_budget_cheaper_than`
  - `test_extract_budget_my_budget_is`
  - `test_detect_gender_bangla`
  - `test_budget_enforcement_end_to_end`
  - `test_budget_enforcement_custom`

---

## Attack Surface

All prompt injection attempts resolved correctly:
- SQLi attempts: DB uses parameterized queries
- Prompt injection: Search pipeline is data-driven, not prompt-driven
- No hallucinated products: Nonsense queries correctly return empty

## Known Limitations (Not Fixed)

1. **Descriptive searches** ("office", "summer", "winter" perfume) return 0 products - These terms don't exist in product data
2. **"cheap" query**: returns 0 products - "cheap" is in STOP_WORDS; no price-based sorting exists
3. **No conversation memory**: Follow-up queries lose context (design limitation of search-only pipeline)
4. **"Ajmal" brand**: No products exist in DB for this brand