"""
Academic Affiliation Checker Package
=====================================

A modular Python tool for checking academic researchers' affiliations
with specified countries using OpenAlex API.
"""

from .config import DEFAULT_CONFIG, COUNTRY_NAMES, OPENALEX_BASE
from .utils import (
    is_generic_institution,
    verify_author_name,
    verify_institution_match,
    verify_author_identity
)
from .api import (
    get_headers,
    search_openalex_author,
    get_author_profile,
    get_author_works
)
from .checkers import (
    get_country_name,
    check_direct_affiliation,
    check_indirect_affiliation
)
from .output import save_to_excel_with_highlight, save_results
from .cli import (
    interactive_country_selection,
    parse_arguments,
    get_config_from_args,
    print_banner,
    print_summary
)

__version__ = "2.0.0"
__author__ = "Academic Data Mining Project"

__all__ = [
    # Config
    'DEFAULT_CONFIG',
    'COUNTRY_NAMES',
    'OPENALEX_BASE',
    # Utils
    'is_generic_institution',
    'verify_author_name',
    'verify_institution_match',
    'verify_author_identity',
    # API
    'get_headers',
    'search_openalex_author',
    'get_author_profile',
    'get_author_works',
    # Checkers
    'get_country_name',
    'check_direct_affiliation',
    'check_indirect_affiliation',
    # Output
    'save_to_excel_with_highlight',
    'save_results',
    # CLI
    'interactive_country_selection',
    'parse_arguments',
    'get_config_from_args',
    'print_banner',
    'print_summary',
]
