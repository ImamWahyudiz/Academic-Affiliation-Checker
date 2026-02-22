"""
Affiliation checking functions
"""

from typing import Dict, List, Tuple, Optional

from .config import COUNTRY_NAMES
from .utils import is_generic_institution


def get_country_name(country_code: str) -> str:
    """Get human-readable country name from ISO code."""
    if not country_code:
        return "Unknown"
    return COUNTRY_NAMES.get(country_code, country_code)


def check_direct_affiliation(
    author_data: Optional[Dict], 
    flagged_countries: List[str]
) -> Tuple[bool, List[str]]:
    """
    Check direct affiliations from author profile.
    
    Args:
        author_data: Author profile data from OpenAlex
        flagged_countries: List of country codes to flag
        
    Returns:
        Tuple of (is_flagged, list_of_evidence)
    """
    if not author_data:
        return False, []
    
    evidence = []
    
    # Check affiliations array (full history)
    affiliations = author_data.get("affiliations") or []
    for aff in affiliations:
        if not isinstance(aff, dict):
            continue
            
        institution = aff.get("institution") or {}
        if not isinstance(institution, dict):
            continue
            
        country_code = institution.get("country_code")
        inst_name = institution.get("display_name", "Unknown Institution")
        inst_type = institution.get("type", "")
        
        # Skip generic institutions that may have incorrect country codes
        if is_generic_institution(inst_name):
            continue
        
        if country_code and country_code in flagged_countries:
            years = aff.get("years") or []
            country_name = get_country_name(country_code)
            
            # Build detailed evidence
            details = []
            
            if years and isinstance(years, list) and len(years) > 0:
                year_range = f"{min(years)}-{max(years)}"
                year_count = len(years)
                if year_count == 1:
                    details.append(f"1 year only ({years[0]})")
                else:
                    details.append(f"{year_count} years ({year_range})")
            
            if inst_type:
                details.append(f"Type: {inst_type}")
            
            # Format evidence string (max ~150 chars)
            ev = f"{inst_name} [{country_name}]"
            if details:
                detail_str = " | ".join(details)
                if len(ev) + len(detail_str) < 150:
                    ev = f"{ev} | {detail_str}"
                else:
                    ev = f"{ev} | {details[0]}"  # At least show years
            
            evidence.append(ev)
    
    # Check last_known_institutions (array)
    last_institutions = author_data.get("last_known_institutions") or []
    for inst in last_institutions:
        if not isinstance(inst, dict):
            continue
            
        inst_name = inst.get("display_name", "Unknown Institution")
        
        # Skip generic institutions
        if is_generic_institution(inst_name):
            continue
            
        country_code = inst.get("country_code")
        if country_code and country_code in flagged_countries:
            country_name = get_country_name(country_code)
            inst_type = inst.get("type", "")
            
            ev = f"{inst_name} [{country_name}] | CURRENT/RECENT"
            if inst_type:
                ev = f"{inst_name} [{country_name}] | CURRENT/RECENT | Type: {inst_type}"
            
            # Avoid duplicates
            if not any(inst_name in e for e in evidence):
                evidence.append(ev)
    
    # Fallback: check last_known_institution (singular/legacy field)
    last_inst = author_data.get("last_known_institution")
    if last_inst and isinstance(last_inst, dict):
        inst_name = last_inst.get("display_name", "Unknown Institution")
        
        # Skip generic institutions
        if not is_generic_institution(inst_name):
            country_code = last_inst.get("country_code")
            if country_code and country_code in flagged_countries:
                country_name = get_country_name(country_code)
                ev = f"{inst_name} [{country_name}] | CURRENT/RECENT"
                if not any(inst_name in e for e in evidence):
                    evidence.append(ev)
    
    return len(evidence) > 0, evidence


def check_indirect_affiliation(
    works: List[Dict], 
    target_author_id: str,
    flagged_countries: List[str]
) -> Tuple[bool, List[str]]:
    """
    Check indirect affiliations through co-authors.
    
    Args:
        works: List of work data from OpenAlex
        target_author_id: The author's OpenAlex ID (to exclude from checking)
        flagged_countries: List of country codes to flag
        
    Returns:
        Tuple of (is_flagged, list_of_evidence)
    """
    if not works:
        return False, []
    
    evidence = []
    checked_institutions = set()
    
    for work in works:
        if not isinstance(work, dict):
            continue
            
        authorships = work.get("authorships") or []
        pub_year = work.get("publication_year", "")
        work_title = work.get("title", "")
        
        # Truncate title if too long
        if work_title and len(work_title) > 80:
            work_title = work_title[:77] + "..."
        
        for authorship in authorships:
            if not isinstance(authorship, dict):
                continue
                
            # Get author info
            author = authorship.get("author") or {}
            if not isinstance(author, dict):
                continue
                
            author_id_raw = author.get("id")
            if not author_id_raw:
                continue
                
            author_id = str(author_id_raw).replace("https://openalex.org/", "")
            
            # Skip the target author themselves
            if author_id == target_author_id:
                continue
            
            # Check co-author's institutions
            institutions = authorship.get("institutions") or []
            for inst in institutions:
                if not isinstance(inst, dict):
                    continue
                    
                country_code = inst.get("country_code")
                inst_id = inst.get("id", "")
                inst_name = inst.get("display_name", "Unknown Institution")
                
                # Skip generic institutions that may have incorrect country codes
                if is_generic_institution(inst_name):
                    continue
                
                if country_code and country_code in flagged_countries:
                    if inst_id and inst_id not in checked_institutions:
                        checked_institutions.add(inst_id)
                        
                        coauthor_name = author.get("display_name", "Unknown Co-author")
                        country_name = get_country_name(country_code)
                        
                        # Include work title in evidence
                        if work_title:
                            ev = f"Co-author: {coauthor_name} at {inst_name} [{country_name}] ({pub_year}) | Paper: \"{work_title}\""
                        else:
                            ev = f"Co-author: {coauthor_name} at {inst_name} [{country_name}] ({pub_year})"
                        evidence.append(ev)
    
    return len(evidence) > 0, evidence
