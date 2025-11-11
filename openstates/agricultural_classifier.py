"""
Agricultural & Farm Worker Bill Classification

Classifies California bills as agricultural/farm worker related based on keyword matching.
See AGRICULTURAL_KEYWORDS.md for detailed rationale and keyword lists.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional
from datetime import datetime


# =============================================================================
# KEYWORD PATTERNS (using regex with word boundaries)
# =============================================================================

# Category: Farm Worker Rights
FARM_WORKER_KEYWORDS = [
    r'\bfarm worker\b',
    r'\bfarmworker\b',
    r'\bagricultural worker\b',
    r'\bagricultural labor\b',
    r'\bagricultural employee\b',
    r'\bagricultural employment\b',
    r'\bcampo\b',
    r'\bcampesino\b',
]

# Category: Safety
SAFETY_KEYWORDS = [
    r'\bheat illness\b',
    r'\bheat stress\b',
    r'\bheat exposure\b',
    r'\bheat safety\b',
    r'\bpesticide\b',
    r'\bchemical exposure\b',
    r'\btoxic substance\b',
    r'\brespiratory illness\b',
    r'\blung disease\b',
    r'\bmusculoskeletal injury\b',
    r'\brepetitive motion\b',
    r'\bpersonal protective equipment\b',
    r'\bPPE\b',
    r'\bsafety equipment\b',
    r'\bshade structure\b',
    r'\bcooling station\b',
    r'\bCal/OSHA\b',
    r'\boccupational safety\b',
    r'\bworkplace safety\b',
    r'\bsafety standard\b',
    r'\binjury prevention\b',
    r'\billness prevention\b',
]

# Category: Union Organizing
UNION_KEYWORDS = [
    r'\bcollective bargaining\b',
    r'\blabor union\b',
    r'\bright to organize\b',
    r'\borganizing rights\b',
    r'\bunion election\b',
    r'\bunion certification\b',
    r'\bcard check\b',
    r'\bmajority signup\b',
    r'\bALRA\b',
    r'\bALRB\b',
    r'\bAgricultural Labor Relations Act\b',
    r'\bAgricultural Labor Relations Board\b',
    r'\bunfair labor practice\b',
    r'\blabor dispute\b',
    r'\bstrike\b',
    r'\bboycott\b',
    r'\bpicketing\b',
    r'\bUFW\b',
    r'\bUnited Farm Workers\b',
    r'\bCesar Chavez\b',
]

# Category: Wages
WAGE_KEYWORDS = [
    r'\bovertime\b',
    r'\bovertime pay\b',
    r'\bovertime exemption\b',
    r'\bminimum wage\b',
    r'\bagricultural wage\b',
    r'\bfarm wage\b',
    r'\bpiece rate\b',
    r'\bpiece-rate\b',
    r'\bhourly wage\b',
    r'\bwage theft\b',
    r'\bunpaid wages\b',
    r'\bpayroll deduction\b',
    r'\bwage statement\b',
    r'\bpayment method\b',
    r'\bdirect deposit\b',
    r'\bbreak time\b',
    r'\bmeal period\b',
    r'\brest period\b',
]

# Category: Immigration
IMMIGRATION_KEYWORDS = [
    r'\bH-2A\b',
    r'\bH2A\b',
    r'\bagricultural visa\b',
    r'\bguest worker\b',
    r'\btemporary worker\b',
    r'\bwork visa\b',
    r'\bemployment visa\b',
    r'\bundocumented\b',
    r'\bunauthorized\b',
    r'\bimmigration status\b',
    r'\bIRCA\b',
    r'\bE-Verify\b',
    r'\bI-9\b',
    r'\bimmigration retaliation\b',
    r'\bnational origin\b',
    r'\blabor contractor\b',
    r'\bfarm labor contractor\b',
    r'\bFLC\b',
]

# Category: Working Conditions
WORKING_CONDITIONS_KEYWORDS = [
    r'\bagricultural housing\b',
    r'\bfarm worker housing\b',
    r'\blabor camp\b',
    r'\bemployer-provided housing\b',
    r'\bgrower housing\b',
    r'\bhousing code\b',
    r'\bhousing standard\b',
    r'\bdormitory\b',
    r'\bbarracks\b',
    r'\bsanitation\b',
    r'\bbathroom\b',
    r'\btoilet\b',
    r'\brestroom\b',
    r'\bhand washing\b',
    r'\bhandwashing\b',
    r'\bwashing station\b',
    r'\bdrinking water\b',
    r'\bpotable water\b',
    r'\bwater access\b',
    r'\bfield conditions\b',
    r'\bfield sanitation\b',
    r'\bagricultural transport\b',
    r'\bcrew transport\b',
    r'\bworker transport\b',
    r'\bvehicle safety\b',
    r'\bpassenger safety\b',
    r'\bworking condition\b',
    r'\bwork environment\b',
    r'\bfield labor\b',
    r'\bharvest work\b',
]

# Exclusion patterns (false positives)
EXCLUSION_KEYWORDS = [
    r'\bcrop insurance\b',
    r'\bwater rights\b',
    r'\bsoil conservation\b',
    r'\bgmo\b',
    r'\bgenetically modified\b',
]


# =============================================================================
# CLASSIFICATION LOGIC
# =============================================================================

def _match_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    Match keywords in text using regex patterns.

    Args:
        text: Text to search (case-insensitive)
        keywords: List of regex patterns

    Returns:
        List of matched keyword patterns
    """
    text_lower = text.lower()
    matches = []

    for pattern in keywords:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matches.append(pattern)

    return matches


def _calculate_priority(categories: List[str], keyword_matches: Dict[str, List[str]]) -> str:
    """
    Calculate priority level based on categories matched and keyword significance.

    High Priority: 3+ categories, contains farm worker or UFW/ALRA
    Medium Priority: 2 categories
    Low Priority: 1 category

    Args:
        categories: List of matched categories
        keyword_matches: Dict of category -> matched keywords

    Returns:
        Priority level: 'high', 'medium', or 'low'
    """
    num_categories = len(categories)

    # Check for high-confidence keywords
    high_confidence_patterns = [
        r'\bfarm worker\b',
        r'\bfarmworker\b',
        r'\bUFW\b',
        r'\bUnited Farm Workers\b',
        r'\bALRA\b',
        r'\bALRB\b',
    ]

    has_high_confidence = False
    for matches in keyword_matches.values():
        for match in matches:
            if any(re.search(pattern, match, re.IGNORECASE) for pattern in high_confidence_patterns):
                has_high_confidence = True
                break
        if has_high_confidence:
            break

    # Priority assignment
    if num_categories >= 3 or (num_categories >= 2 and has_high_confidence):
        return 'high'
    elif num_categories == 2:
        return 'medium'
    else:
        return 'low'


def classify_agricultural_bill(
    title: str,
    description: Optional[str] = None,
    subjects: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Classify a bill as agricultural/farm worker related.

    Args:
        title: Bill title
        description: Bill description (optional)
        subjects: List of LegiScan subjects (optional)

    Returns:
        Classification dict if agricultural, None otherwise

    Example return:
    {
        "is_agricultural": True,
        "categories": ["farm_worker_rights", "safety"],
        "priority": "high",
        "manually_curated": False,
        "notes": None,
        "auto_detected_keywords": ["farm worker", "heat illness"],
        "classification_date": "2025-01-11T12:00:00Z"
    }
    """
    # Combine text sources
    text = title or ""
    if description:
        text += " " + description

    # Check exclusion patterns first
    exclusion_matches = _match_keywords(text, EXCLUSION_KEYWORDS)

    # Check for agricultural keywords but without labor/worker context
    # If we have exclusions but no strong labor indicators, skip
    if exclusion_matches:
        labor_indicators = [
            r'\bworker\b', r'\blabor\b', r'\bemployee\b', r'\bwage\b', r'\bsafety\b'
        ]
        has_labor_context = any(re.search(p, text.lower()) for p in labor_indicators)
        if not has_labor_context:
            return None  # False positive

    # Match keywords by category
    categories = []
    keyword_matches = {}
    all_matched_keywords = []

    # Farm Worker Rights
    matches = _match_keywords(text, FARM_WORKER_KEYWORDS)
    if matches:
        categories.append('farm_worker_rights')
        keyword_matches['farm_worker_rights'] = matches
        all_matched_keywords.extend(matches)

    # Safety
    matches = _match_keywords(text, SAFETY_KEYWORDS)
    if matches:
        # Only add safety if we have agricultural context
        has_ag_context = any(
            re.search(p, text.lower()) for p in
            [r'\bagricultural\b', r'\bfarm\b', r'\bgrower\b', r'\bharvest\b']
        )
        if has_ag_context or 'farm_worker_rights' in categories:
            categories.append('safety')
            keyword_matches['safety'] = matches
            all_matched_keywords.extend(matches)

    # Union Organizing
    matches = _match_keywords(text, UNION_KEYWORDS)
    if matches:
        categories.append('union_organizing')
        keyword_matches['union_organizing'] = matches
        all_matched_keywords.extend(matches)

    # Wages
    matches = _match_keywords(text, WAGE_KEYWORDS)
    if matches:
        # Check for agricultural context
        has_ag_context = any(
            re.search(p, text.lower()) for p in
            [r'\bagricultural\b', r'\bfarm\b', r'\bgrower\b']
        )
        if has_ag_context or 'farm_worker_rights' in categories:
            categories.append('wages')
            keyword_matches['wages'] = matches
            all_matched_keywords.extend(matches)

    # Immigration
    matches = _match_keywords(text, IMMIGRATION_KEYWORDS)
    if matches:
        # Check for agricultural context (H-2A is strong indicator on its own)
        has_h2a = any(re.search(r'\bH-?2A\b', text, re.IGNORECASE) for _ in [1])
        has_ag_context = any(
            re.search(p, text.lower()) for p in
            [r'\bagricultural\b', r'\bfarm\b', r'\bgrower\b']
        )
        if has_h2a or has_ag_context or 'farm_worker_rights' in categories:
            categories.append('immigration')
            keyword_matches['immigration'] = matches
            all_matched_keywords.extend(matches)

    # Working Conditions
    matches = _match_keywords(text, WORKING_CONDITIONS_KEYWORDS)
    if matches:
        # Check for agricultural context
        has_ag_context = any(
            re.search(p, text.lower()) for p in
            [r'\bagricultural\b', r'\bfarm\b', r'\bgrower\b']
        )
        if has_ag_context or 'farm_worker_rights' in categories:
            categories.append('working_conditions')
            keyword_matches['working_conditions'] = matches
            all_matched_keywords.extend(matches)

    # Check LegiScan subjects if provided
    if subjects and not categories:
        ag_subjects = ['Agriculture', 'Labor and Employment', 'Labor Relations',
                      'Occupational Safety and Health', 'Immigration', 'Housing']
        has_ag_subject = any(s in subjects for s in ag_subjects)

        # If we have ag subject + some keywords but didn't trigger categories, check again
        if has_ag_subject and all_matched_keywords:
            # Give it another chance with looser requirements
            if len(all_matched_keywords) >= 2:
                # Re-add the most relevant category
                if 'farm' in text.lower() or 'agricult' in text.lower():
                    categories.append('farm_worker_rights')

    # Return None if no categories matched
    if not categories:
        return None

    # Calculate priority
    priority = _calculate_priority(categories, keyword_matches)

    # Build classification object
    classification = {
        'is_agricultural': True,
        'categories': categories,
        'priority': priority,
        'manually_curated': False,
        'notes': None,
        'auto_detected_keywords': list(set(all_matched_keywords[:10])),  # Limit to 10 unique
        'classification_date': datetime.utcnow().isoformat() + 'Z'
    }

    return classification


# =============================================================================
# BULK CLASSIFICATION HELPERS
# =============================================================================

def classify_bill_from_db_row(row: Dict) -> Optional[Dict]:
    """
    Classify a bill from a database row.

    Args:
        row: Database row with 'title', 'description', optional 'subjects'

    Returns:
        Classification dict or None
    """
    title = row.get('title', '')
    description = row.get('description')
    subjects = row.get('subjects')  # Could be JSON array

    return classify_agricultural_bill(title, description, subjects)
