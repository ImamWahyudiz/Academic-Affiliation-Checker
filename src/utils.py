"""
Utility functions for name and institution verification
"""

import re
from typing import Dict, Tuple, Set

from .config import GENERIC_INSTITUTION_PATTERNS


def is_generic_institution(institution_name: str) -> bool:
    """
    Check if an institution name is too generic and should be excluded.
    
    Args:
        institution_name: Name of the institution
        
    Returns:
        True if institution should be excluded (generic), False otherwise
    """
    if not institution_name:
        return False
    
    name_lower = institution_name.lower().strip()
    
    for pattern in GENERIC_INSTITUTION_PATTERNS:
        if pattern in name_lower:
            return True
    
    return False


def _normalize_name(name: str) -> str:
    """Normalize name: lowercase, remove punctuation except hyphens."""
    return re.sub(r'[^\w\s\-]', '', name.lower().strip())


def _get_name_variants(name: str) -> Set[str]:
    """Get all reasonable variants of a name."""
    name = _normalize_name(name)
    variants = {name}
    
    # Add version without hyphens (merged)
    if '-' in name:
        variants.add(name.replace('-', ''))
    
    # Add individual parts if hyphenated
    if '-' in name:
        for part in name.split('-'):
            if len(part) > 1:
                variants.add(part)
    
    return variants


def verify_author_name(
    expected_first: str, 
    expected_last: str, 
    actual_name: str,
    threshold: float = 0.5
) -> bool:
    """
    Verify that the OpenAlex author name matches the expected name.
    
    This helps prevent false positives from ID mismatches where different
    authors with similar names get confused.
    
    Args:
        expected_first: Expected first name
        expected_last: Expected last name
        actual_name: Actual display name from OpenAlex
        threshold: Minimum match ratio (0.0-1.0)
        
    Returns:
        True if names match sufficiently, False otherwise
    """
    if not actual_name:
        return False
    
    expected_first = _normalize_name(expected_first)
    expected_last = _normalize_name(expected_last)
    actual_name_normalized = _normalize_name(actual_name)
    
    # Split actual name into parts
    actual_parts = set()
    for part in actual_name_normalized.split():
        actual_parts.add(part)
        # Handle merged hyphenated names
        if '-' in part:
            actual_parts.add(part.replace('-', ''))
            for subpart in part.split('-'):
                if len(subpart) > 1:
                    actual_parts.add(subpart)
    
    # Get expected name variants
    expected_first_variants = _get_name_variants(expected_first)
    expected_last_variants = _get_name_variants(expected_last)
    
    # Check if last name matches (strict: must be a complete word/part)
    last_name_match = False
    for exp_last in expected_last_variants:
        if exp_last in actual_parts:
            last_name_match = True
            break
    
    # Check if first name matches
    first_name_match = False
    for exp_first in expected_first_variants:
        # Skip very short variants unless they're the only option
        if len(exp_first) < 2 and len(expected_first_variants) > 1:
            continue
            
        # Check full first name as complete word
        if exp_first in actual_parts:
            first_name_match = True
            break
            
        # Check if first name is part of a merged name in actual
        for actual_part in actual_parts:
            if len(exp_first) >= 3 and actual_part.startswith(exp_first):
                first_name_match = True
                break
        
        if first_name_match:
            break
    
    # Check initials if first name doesn't match yet
    if not first_name_match and len(expected_first) >= 1:
        first_initial = expected_first[0]
        for part in actual_parts:
            if len(part) <= 2 and part[0] == first_initial:
                first_name_match = True
                break
            if part[0] == first_initial and len(part) > len(expected_first) * 0.5:
                first_name_match = True
                break
    
    # Both must match for confirmation
    if len(expected_first.replace(' ', '')) <= 2 and last_name_match:
        return True
    
    return last_name_match and first_name_match


def _normalize_institution(name: str) -> str:
    """Normalize institution name for comparison."""
    if not name:
        return ""
    # Lowercase, remove punctuation
    name = re.sub(r'[^\w\s]', '', name.lower().strip())
    # Remove common words that don't help matching
    remove_words = ['university', 'of', 'the', 'institute', 'college', 
                   'school', 'department', 'faculty', 'center', 'centre',
                   'national', 'state', 'technical', 'technology']
    words = name.split()
    filtered = [w for w in words if w not in remove_words and len(w) > 2]
    return ' '.join(filtered) if filtered else name


def _get_institution_keywords(name: str) -> Set[str]:
    """Extract key identifying words from institution name."""
    normalized = _normalize_institution(name)
    return set(normalized.split())


def verify_institution_match(
    expected_institution: str,
    author_data: Dict
) -> Tuple[bool, float]:
    """
    Verify that the author's institution history contains the expected institution.
    
    Args:
        expected_institution: Institution name from input data
        author_data: Author profile from OpenAlex
        
    Returns:
        Tuple of (is_match, confidence_score)
    """
    if not expected_institution or not author_data:
        return True, 0.0
    
    expected_normalized = _normalize_institution(expected_institution)
    expected_keywords = _get_institution_keywords(expected_institution)
    
    if not expected_keywords:
        return True, 0.0
    
    # Collect all institution names from author's history
    author_institutions = set()
    
    # From affiliations
    affiliations = author_data.get("affiliations") or []
    for aff in affiliations:
        inst = aff.get("institution") or {}
        inst_name = inst.get("display_name", "")
        if inst_name:
            author_institutions.add(inst_name)
    
    # From last_known_institutions
    last_insts = author_data.get("last_known_institutions") or []
    for inst in last_insts:
        if inst:
            inst_name = inst.get("display_name", "")
            if inst_name:
                author_institutions.add(inst_name)
    
    # Check for matches
    best_score = 0.0
    
    for inst_name in author_institutions:
        inst_normalized = _normalize_institution(inst_name)
        inst_keywords = _get_institution_keywords(inst_name)
        
        # Check exact normalized match
        if expected_normalized == inst_normalized:
            return True, 1.0
        
        # Check if expected is contained in author's institution or vice versa
        if expected_normalized in inst_normalized or inst_normalized in expected_normalized:
            best_score = max(best_score, 0.9)
            continue
        
        # Check keyword overlap (Jaccard similarity)
        if expected_keywords and inst_keywords:
            intersection = expected_keywords & inst_keywords
            union = expected_keywords | inst_keywords
            if union:
                jaccard = len(intersection) / len(union)
                if jaccard > 0.3:
                    best_score = max(best_score, jaccard)
    
    return best_score >= 0.3, best_score


def verify_author_identity(
    expected_first: str,
    expected_last: str,
    expected_institution: str,
    author_data: Dict
) -> Tuple[bool, str]:
    """
    Comprehensive author identity verification using name AND institution.
    
    Args:
        expected_first: Expected first name
        expected_last: Expected last name
        expected_institution: Expected current institution
        author_data: Author profile from OpenAlex
        
    Returns:
        Tuple of (is_verified, reason)
    """
    if not author_data:
        return False, "No author data"
    
    actual_name = author_data.get("display_name", "")
    
    # Step 1: Check name match
    name_match = verify_author_name(expected_first, expected_last, actual_name)
    
    # Step 2: Check institution match
    inst_match, inst_score = verify_institution_match(expected_institution, author_data)
    
    # Decision logic
    if name_match:
        if inst_match:
            return True, f"Name and institution verified (score: {inst_score:.2f})"
        elif not expected_institution:
            return True, "Name verified (no institution to check)"
        else:
            return True, f"Name verified, institution not found in history (may be outdated)"
    else:
        return False, f"Name mismatch (expected: '{expected_first} {expected_last}', got: '{actual_name}')"
