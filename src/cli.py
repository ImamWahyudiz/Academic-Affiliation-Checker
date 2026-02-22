"""
Command-line interface module
"""

import argparse
from typing import List

from .config import COUNTRY_NAMES, DEFAULT_CONFIG


def interactive_country_selection() -> List[str]:
    """
    Display interactive menu for country selection.
    
    Returns:
        List of selected country codes
    """
    print("\n" + "=" * 70)
    print("SELECT COUNTRIES TO CHECK FOR AFFILIATIONS")
    print("=" * 70)
    
    # Display country codes in compact columns
    items = list(COUNTRY_NAMES.items())
    cols = 4  # Number of columns
    col_width = 17
    
    for i in range(0, len(items), cols):
        row = items[i:i+cols]
        row_str = "".join([f"{code}={name:<{col_width-3}}" for code, name in row])
        print(f"  {row_str}")
    
    print("-" * 70)
    print("Input: kode negara dipisah spasi, contoh: IL IR RU")
    print("-" * 70)
    
    while True:
        user_input = input(">>> ").strip().upper()
        
        if not user_input:
            print("[!] Masukkan minimal 1 kode negara.")
            continue
        
        codes = user_input.split()
        valid_codes = []
        invalid_codes = []
        
        for code in codes:
            if code in COUNTRY_NAMES:
                valid_codes.append(code)
            else:
                invalid_codes.append(code)
        
        if invalid_codes:
            print(f"[!] Kode tidak dikenal: {', '.join(invalid_codes)}")
        
        if valid_codes:
            return valid_codes
        else:
            print("[!] Tidak ada kode valid. Coba lagi.")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Academic Affiliation Background Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python affiliation_checker.py -i Data.csv -c IL IR RU
  python affiliation_checker.py --interactive
  python affiliation_checker.py -i candidates.csv -o results.xlsx -c IL IR --works 50
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        default=DEFAULT_CONFIG["input_file"],
        help=f"Input CSV file (default: {DEFAULT_CONFIG['input_file']})"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_CONFIG["output_file"],
        help=f"Output file (default: {DEFAULT_CONFIG['output_file']})"
    )
    
    parser.add_argument(
        "-c", "--countries",
        nargs="+",
        help="Country codes to flag (e.g., IL IR RU). If not provided, interactive selection."
    )
    
    parser.add_argument(
        "--works",
        type=int,
        default=DEFAULT_CONFIG["max_works_to_check"],
        help=f"Max works to check for indirect affiliations (default: {DEFAULT_CONFIG['max_works_to_check']})"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_CONFIG["api_delay"],
        help=f"Delay between API requests in seconds (default: {DEFAULT_CONFIG['api_delay']})"
    )
    
    parser.add_argument(
        "--email",
        default=None,
        help="Email for OpenAlex polite pool (faster API access)"
    )
    
    return parser.parse_args()


def get_config_from_args(args: argparse.Namespace, selected_countries: List[str] = None) -> dict:
    """
    Build configuration dictionary from parsed arguments.
    
    Args:
        args: Parsed command line arguments
        selected_countries: Override for country selection (optional)
        
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    config["input_file"] = args.input
    config["output_file"] = args.output
    config["max_works_to_check"] = args.works
    config["api_delay"] = args.delay
    
    if args.email:
        config["user_agent"] = f"mailto:{args.email}"
    
    # Handle country selection - prefer passed parameter over args
    if selected_countries:
        config["flagged_countries"] = selected_countries
    elif args.countries:
        config["flagged_countries"] = [c.upper() for c in args.countries]
    else:
        config["flagged_countries"] = DEFAULT_CONFIG["flagged_countries"]
    
    return config


def print_banner():
    """Print program banner."""
    print("=" * 70)
    print("ACADEMIC AFFILIATION BACKGROUND CHECKER")
    print("Using OpenAlex API")
    print("=" * 70)


def print_summary(
    total_rows: int,
    candidates_with_id: int,
    flagged_count: int,
    direct_count: int,
    indirect_count: int,
    flagged_candidates: list,
    output_file: str
):
    """Print final summary of background check results."""
    clean_count = candidates_with_id - flagged_count
    
    print("\n" + "=" * 70)
    print("BACKGROUND CHECK SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal rows loaded: {total_rows}")
    print(f"Candidates checked: {candidates_with_id}")
    
    if candidates_with_id > 0:
        print(f"Clean (no flags): {clean_count} ({clean_count/candidates_with_id*100:.1f}%)")
        print(f"Flagged: {flagged_count} ({flagged_count/candidates_with_id*100:.1f}%)")
    else:
        print(f"Clean (no flags): {clean_count}")
        print(f"Flagged: {flagged_count}")
    
    print(f"  - Direct affiliation: {direct_count}")
    print(f"  - Indirect (co-author): {indirect_count}")
    
    if flagged_candidates:
        print("\n" + "-" * 70)
        print("FLAGGED CANDIDATES:")
        print("-" * 70)
        
        for i, fc in enumerate(flagged_candidates, 1):
            print(f"\n{i}. {fc['Name']}")
            print(f"   Type: {fc['Type']}")
            print(f"   Evidence: {fc['Evidence']}...")
    
    print(f"\n[OUTPUT] {output_file}")
    print("\n[DONE] Background check complete!")
    print("=" * 70)
