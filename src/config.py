"""
Configuration module for Academic Affiliation Checker
"""

# Default configuration
DEFAULT_CONFIG = {
    "input_file": "Data.csv",
    "output_file": "Vetted_Output.csv",
    "flagged_countries": ["IL", "IR"],  # ISO 3166-1 alpha-2 codes
    "max_works_to_check": 30,
    "api_delay": 0.2,
    "user_agent": "mailto:academic-checker@example.com"
}

# Country code to name mapping (ISO 3166-1 alpha-2)
COUNTRY_NAMES = {
    "IL": "Israel",
    "IR": "Iran",
    "RU": "Russia",
    "CN": "China",
    "KP": "North Korea",
    "SY": "Syria",
    "CU": "Cuba",
    "BY": "Belarus",
    "VE": "Venezuela",
    "MM": "Myanmar",
    "AF": "Afghanistan",
    "IQ": "Iraq",
    "LY": "Libya",
    "SD": "Sudan",
    "YE": "Yemen",
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "KR": "South Korea",
    "AU": "Australia",
    "CA": "Canada",
    "IN": "India",
    "BR": "Brazil",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "SG": "Singapore",
    "SA": "Saudi Arabia",
    "AE": "UAE",
    "QA": "Qatar",
    "EG": "Egypt",
    "TR": "Turkey",
    "PK": "Pakistan",
}

# Generic institution patterns to exclude (false positive prevention)
# OpenAlex sometimes incorrectly tags these with wrong country codes
GENERIC_INSTITUTION_PATTERNS = [
    "ministry of education",
    "ministry of science",
    "ministry of health",
    "ministry of",
    "department of education",
    "national science foundation",
    "government of",
    "state council",
]

# OpenAlex API base URL
OPENALEX_BASE = "https://api.openalex.org"
