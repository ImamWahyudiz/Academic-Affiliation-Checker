"""
OpenAlex API interface module
"""

import requests
from typing import Dict, List, Optional

from .config import OPENALEX_BASE


def get_headers(user_agent: str) -> Dict:
    """Get request headers with polite user agent."""
    return {"User-Agent": user_agent}


def search_openalex_author(first_name: str, last_name: str, headers: Dict) -> Optional[str]:
    """
    Search for an author in OpenAlex by name.
    
    Args:
        first_name: Author's first name
        last_name: Author's last name
        headers: Request headers
        
    Returns:
        OpenAlex ID (without URL prefix) or None if not found
    """
    query = f"{first_name}+{last_name}"
    url = f"{OPENALEX_BASE}/authors?search={query}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if results and len(results) > 0:
            author = results[0]
            openalex_id = author.get("id", "")
            if openalex_id:
                return openalex_id.replace("https://openalex.org/", "")
        return None
    except requests.RequestException as e:
        print(f"    [API ERROR] Search: {e}")
        return None


def get_author_profile(openalex_id: str, headers: Dict) -> Optional[Dict]:
    """
    Fetch author profile from OpenAlex.
    
    Args:
        openalex_id: OpenAlex author ID
        headers: Request headers
        
    Returns:
        Author data dict or None
    """
    if not openalex_id:
        return None
        
    url = f"{OPENALEX_BASE}/authors/{openalex_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"    [API ERROR] Author profile: {e}")
        return None


def get_author_works(openalex_id: str, headers: Dict, per_page: int = 30) -> List[Dict]:
    """
    Fetch recent works from an author.
    
    Args:
        openalex_id: OpenAlex author ID
        headers: Request headers
        per_page: Number of works to fetch
        
    Returns:
        List of work dictionaries
    """
    if not openalex_id:
        return []
        
    url = f"{OPENALEX_BASE}/works"
    params = {
        "filter": f"author.id:{openalex_id}",
        "sort": "publication_date:desc",
        "per-page": per_page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        print(f"    [API ERROR] Author works: {e}")
        return []
