"""Product attribute extraction from data JSON.

Extracts structured attributes (notes, longevity, projection, etc.)
from the `data.fragrance_details` JSON blob in each product dict.
"""

import json
from typing import Any


def _get_data(product: dict[str, Any]) -> dict[str, Any]:
    raw = product.get("data")
    if not raw:
        return {}
    try:
        return json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return {}


def extract_fragrance_details(product: dict[str, Any]) -> dict[str, Any]:
    """Extract fragrance_details sub-object from product data JSON."""
    data = _get_data(product)
    if not data:
        return {}
    return data.get("fragrance_details") or {}


def get_product_attributes(product: dict[str, Any]) -> dict[str, Any]:
    """Return all fragrance attributes with None for missing values."""
    fd = extract_fragrance_details(product)
    notes_obj = fd.get("notes") or {}
    return {
        "type": fd.get("type") or None,
        "longevity": fd.get("longevity") or None,
        "sillage": fd.get("sillage") or None,
        "best_time": fd.get("bestTime") or None,
        "notes_top": (notes_obj.get("top") or None) if isinstance(notes_obj, dict) else None,
        "notes_middle": (notes_obj.get("middle") or None) if isinstance(notes_obj, dict) else None,
        "notes_base": (notes_obj.get("base") or None) if isinstance(notes_obj, dict) else None,
        "scent_family": fd.get("scent_family") or None,
        "occasion": fd.get("occasion") or None,
        "performance": fd.get("performance") or None,
        "authenticity": fd.get("authenticity") or None,
        "product_origin": fd.get("product_origin") or None,
        "strength": fd.get("strength") or None,
    }


def has_any_attribute(product: dict[str, Any]) -> bool:
    """Return True if the product has at least one non-empty attribute."""
    attrs = get_product_attributes(product)
    return any(v for v in attrs.values() if v)


def _format_notes(product: dict[str, Any]) -> str | None:
    """Format notes into a single comma-separated string if any exist."""
    attrs = get_product_attributes(product)
    parts = []
    if attrs["notes_top"]:
        parts.append(f"Top: {', '.join(attrs['notes_top'])}")
    if attrs["notes_middle"]:
        parts.append(f"Middle: {', '.join(attrs['notes_middle'])}")
    if attrs["notes_base"]:
        parts.append(f"Base: {', '.join(attrs['notes_base'])}")
    return " | ".join(parts) if parts else None


def format_product_attributes(product: dict[str, Any]) -> str | None:
    """Return compact attribute string or None if no attributes exist."""
    fd = extract_fragrance_details(product)
    parts = []

    ft = (fd.get("type") or "").strip()
    if ft:
        parts.append(f"Type: {ft}")

    lo = (fd.get("longevity") or "").strip()
    if lo:
        parts.append(f"Longevity: {lo}")

    si = (fd.get("sillage") or "").strip()
    if si:
        parts.append(f"Sillage: {si}")

    bt = (fd.get("bestTime") or "").strip()
    if bt:
        parts.append(f"Best for: {bt}")

    sf = fd.get("scent_family")
    if sf and isinstance(sf, list) and sf:
        parts.append(f"Scent: {', '.join(sf)}")

    oc = fd.get("occasion")
    if oc and isinstance(oc, list) and oc:
        parts.append(f"Occasion: {', '.join(oc)}")

    pf = fd.get("performance")
    if pf and isinstance(pf, list) and pf:
        parts.append(f"Performance: {', '.join(pf)}")

    auth = fd.get("authenticity")
    if auth and isinstance(auth, str) and auth.strip():
        parts.append(f"Authenticity: {auth.strip()}")

    notes_str = _format_notes(product)
    if notes_str:
        parts.append(notes_str)

    return " | ".join(parts) if parts else None
