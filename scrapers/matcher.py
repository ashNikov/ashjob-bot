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


def is_relevant_strict(title: str) -> bool:
    """Title-only match for noisy sources (e.g. RemoteOK spam-tags everything)."""
    title_l = (title or "").lower()
    return any(kw in title_l for kw in TITLE_KEYWORDS)


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


def passes(title: str, tags: list, location: str, posted: str = "") -> bool:
    """A job survives only if it clears relevance, geo, AND freshness."""
    return is_relevant(title, tags) and is_geo_ok(location) and is_fresh(posted)


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
    # explicit mid-level / junior markers -> always good (Uwem's level)
    if any(m in t for m in ["mid-level", "mid level", "midlevel", "junior",
                            "intern", "associate", "entry", " ii ", "-ii",
                            "intermediate"]):
        return "good"
    if any(k in t for k in SENIORITY_DROP):
        return "drop"
    if any(k in t for k in SENIORITY_STRETCH):
        return "stretch"
    return "good"


# --- GATE 4: FRESHNESS ---
# Drop jobs posted more than MAX_AGE_DAYS ago.
from datetime import datetime, timezone
from dateutil import parser as _dateparser

MAX_AGE_DAYS = 4


def is_fresh(posted: str) -> bool:
    """True if the job was posted within MAX_AGE_DAYS. Unknown date -> keep (fail-open)."""
    if not posted:
        return True  # no date info -> don't drop it on that basis
    try:
        dt = _dateparser.parse(posted)
        # make tz-aware for safe comparison
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400
        return age_days <= MAX_AGE_DAYS
    except Exception:
        return True  # unparseable -> keep, don't lose a job over a date quirk
