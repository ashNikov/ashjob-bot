"""
Shared filters — used by all scrapers.
Two gates: relevance (is it DevOps?) and geo (can Uwem be hired?).
A job must pass BOTH.
"""

# --- GATE 1: RELEVANCE ---
# Strong signals in the TITLE — the main qualifier now
TITLE_KEYWORDS = [
    "devops", "devsecops", "sre", "site reliability",
    "cloud engineer", "cloud security", "cloud infrastructure",
    "platform engineer", "infrastructure engineer",
    "cloud architect", "security engineer",
]

# Strict tags — must be an exact devops-family tag, not generic "cloud"
STRICT_TAGS = {"devops", "devsecops", "sre", "kubernetes", "terraform"}


def is_relevant(title: str, tags: list) -> bool:
    title_l = (title or "").lower()
    tags_l = {t.lower() for t in (tags or [])}
    if any(kw in title_l for kw in TITLE_KEYWORDS):
        return True
    if tags_l & STRICT_TAGS:
        return True
    return False


# --- GATE 2: GEO ---
# KEEP if location shows any of these — open to Uwem in Nigeria
GEO_ALLOW = [
    "africa", "worldwide", "anywhere", "global", "remote",
    "nigeria", "emea", "any location", "international",
]

# DROP if location is locked to a region that excludes Nigeria,
# UNLESS an allow-term is also present (e.g. "USA, Africa" stays).
GEO_BLOCK = [
    "usa only", "us only", "united states only", "u.s. only",
    "brazil", "mexico", "uruguay", "canada only",
    "us-based", "must reside in", "authorized to work in the u",
]


def is_geo_ok(location: str) -> bool:
    loc = (location or "").lower().strip()
    if not loc:
        return False  # unknown location — be conservative, drop it

    has_allow = any(a in loc for a in GEO_ALLOW)
    has_block = any(b in loc for b in GEO_BLOCK)

    # If it explicitly allows a region that includes us, keep it —
    # even if a blocked region is also listed (multi-region roles).
    if has_allow:
        return True
    # No allow term, and it's locked to a blocked region → drop
    if has_block:
        return False
    # No signal either way — a bare country like "USA" with no allow term.
    # Conservative: if it names a single non-African country, drop.
    single_country_blocks = ["usa", "united states", "u.s.", "europe",
                             "uk", "germany", "france", "india", "australia"]
    if any(c in loc for c in single_country_blocks):
        return False
    return False  # default drop when unsure — surgical, not bulldozer


def passes(title: str, tags: list, location: str) -> bool:
    """A job survives only if it clears BOTH gates."""
    return is_relevant(title, tags) and is_geo_ok(location)


# --- GATE 3: SENIORITY ---
# Over-level for ~2 yrs experience — drop these
SENIORITY_DROP = [
    "director", "vp ", "vice president", "head of", "principal",
    "staff ", "manager", " lead", "lead ", "chief", "architect",
]
# A reach but applyable — flag, don't hide
SENIORITY_STRETCH = ["senior", "sr.", "sr ", "iv", " iii"]


def seniority_bucket(title: str) -> str:
    """Return 'good', 'stretch', or 'drop' based on title level."""
    t = (title or "").lower()
    if any(k in t for k in SENIORITY_DROP):
        return "drop"
    if any(k in t for k in SENIORITY_STRETCH):
        return "stretch"
    return "good"
