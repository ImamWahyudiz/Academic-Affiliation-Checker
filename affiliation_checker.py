#!/usr/bin/env python3
"""
Academic Affiliation Background Checker using OpenAlex API
============================================================

Main entry point for the modular affiliation checker.
All supporting modules are organized in the src/ package.

Features:
- Uses OpenAlex API (free, no API key required)
- Checks direct affiliations (author profile)
- Checks indirect affiliations (co-authors)
- Exports results to CSV/Excel with highlighting
- Author identity verification (name + institution)
- Generic institution filtering

Usage:
    python affiliation_checker.py -i candidates.csv -c IL IR
    python affiliation_checker.py -i data.csv -c RU CN --works 50

Author: Academic Data Mining Project
License: MIT
"""

import time
from typing import Dict

import pandas as pd

# Import from modular src package
from src import (
    # Config
    DEFAULT_CONFIG,
    COUNTRY_NAMES,
    # Utils
    verify_author_identity,
    # API
    get_headers,
    search_openalex_author,
    get_author_profile,
    get_author_works,
    # Checkers
    get_country_name,
    check_direct_affiliation,
    check_indirect_affiliation,
    # Output
    save_to_excel_with_highlight,
    # CLI
    interactive_country_selection,
    parse_arguments,
    get_config_from_args,
    print_banner,
    print_summary
)


# ============================================================================
# MAIN PROCESSING FUNCTIONS
# ============================================================================

def process_candidate(
    index: int, 
    row: pd.Series, 
    df: pd.DataFrame, 
    total_rows: int,
    config: Dict,
    headers: Dict,
    display_num: int = 0
) -> bool:
    """
    Process a single candidate for background check.
    
    Args:
        index: DataFrame row index
        row: Row data
        df: DataFrame (modified in place)
        total_rows: Total number of rows
        config: Configuration dictionary
        headers: Request headers
        display_num: Display number for progress (optional)
        
    Returns:
        True if flagged, False otherwise
    """
    first_name = str(row.get("First Name", "")).strip()
    last_name = str(row.get("Last Name", "")).strip()
    openalex_id = str(row.get("OpenAlex_ID", "")).strip()
    current_institution = str(row.get("Current Institution", "")).strip()
    
    flagged_countries = config["flagged_countries"]
    max_works = config["max_works_to_check"]
    api_delay = config["api_delay"]
    
    progress = display_num if display_num > 0 else index + 1
    print(f"\n[{progress}/{total_rows}] Checking: {first_name} {last_name}")
    print(f"    OpenAlex ID: {openalex_id}")
    if current_institution:
        print(f"    Institution: {current_institution}")
    
    # Initialize results
    flag_result = "No"
    affiliation_type = "None"
    flag_evidence = ""
    
    # ========================================================================
    # STEP 0: Verify Author Identity (Name + Institution)
    # ========================================================================
    author_data = get_author_profile(openalex_id, headers)
    time.sleep(api_delay)
    
    if author_data:
        actual_name = author_data.get("display_name", "")
        
        # Use comprehensive identity verification
        is_verified, verify_reason = verify_author_identity(
            first_name, last_name, current_institution, author_data
        )
        
        if not is_verified:
            print(f"    [WARNING] {verify_reason}")
            print(f"    [SKIP] Skipping affiliation check due to potential ID mismatch")
            df.at[index, "Flag"] = "No"
            df.at[index, "Affiliation_Type"] = "None"
            df.at[index, "Flag_Evidence"] = f"ID Mismatch: OpenAlex shows '{actual_name}'"
            return False
        
        print(f"    OpenAlex Name: {actual_name} [{verify_reason}]")
    
    # ========================================================================
    # STEP 1: Direct Affiliation Check
    # ========================================================================
    print("    [STEP 1] Checking direct affiliations...")
    
    if author_data:
        is_direct, direct_evidence = check_direct_affiliation(author_data, flagged_countries)
        
        if is_direct:
            flag_result = "Yes"
            affiliation_type = "Direct"
            flag_evidence = "; ".join(direct_evidence)
            print(f"    [FLAG] DIRECT affiliation found!")
            for ev in direct_evidence[:5]:
                print(f"           - {ev}")
            
            df.at[index, "Flag"] = flag_result
            df.at[index, "Affiliation_Type"] = affiliation_type
            df.at[index, "Flag_Evidence"] = flag_evidence
            return True
        else:
            print("    [OK] No direct affiliation found")
    else:
        print("    [WARNING] Could not fetch author profile")
    
    # ========================================================================
    # STEP 2: Indirect Affiliation Check (Co-authors)
    # ========================================================================
    print(f"    [STEP 2] Checking indirect affiliations (last {max_works} works)...")
    
    works = get_author_works(openalex_id, headers, max_works)
    time.sleep(api_delay)
    
    if works:
        print(f"    Found {len(works)} works to check")
        
        is_indirect, indirect_evidence = check_indirect_affiliation(
            works, openalex_id, flagged_countries
        )
        
        if is_indirect:
            flag_result = "Yes"
            affiliation_type = "Indirect (Co-author)"
            flag_evidence = "; ".join(indirect_evidence[:5])
            print(f"    [FLAG] INDIRECT affiliation found through co-authors!")
            for ev in indirect_evidence[:3]:
                print(f"           - {ev}")
            if len(indirect_evidence) > 3:
                print(f"           - ... and {len(indirect_evidence) - 3} more")
        else:
            print("    [OK] No indirect affiliation found")
    else:
        print("    [INFO] No works found")
    
    # Update DataFrame
    df.at[index, "Flag"] = flag_result
    df.at[index, "Affiliation_Type"] = affiliation_type
    df.at[index, "Flag_Evidence"] = flag_evidence
    
    return flag_result == "Yes"


def ensure_openalex_ids(df: pd.DataFrame, config: Dict, headers: Dict) -> pd.DataFrame:
    """
    Ensure all rows have OpenAlex IDs, searching if necessary.
    
    Args:
        df: Input DataFrame
        config: Configuration dictionary
        headers: Request headers
        
    Returns:
        DataFrame with OpenAlex_ID column populated
    """
    if "OpenAlex_ID" not in df.columns:
        print("[INFO] Column 'OpenAlex_ID' not found. Searching for authors...")
        df["OpenAlex_ID"] = None
    
    api_delay = config["api_delay"]
    needs_search = df["OpenAlex_ID"].isna() | (df["OpenAlex_ID"] == "")
    
    if needs_search.sum() > 0:
        print(f"[INFO] Searching OpenAlex IDs for {needs_search.sum()} candidates...")
        
        for index, row in df[needs_search].iterrows():
            first_name = str(row.get("First Name", "")).strip()
            last_name = str(row.get("Last Name", "")).strip()
            
            if first_name and last_name:
                print(f"  Searching: {first_name} {last_name}...", end=" ")
                openalex_id = search_openalex_author(first_name, last_name, headers)
                
                if openalex_id:
                    df.at[index, "OpenAlex_ID"] = openalex_id
                    print(f"Found: {openalex_id}")
                else:
                    print("Not found")
                    
                time.sleep(api_delay)
        
        print("[INFO] OpenAlex ID search complete.")
    
    return df


def run_background_check(config: Dict) -> None:
    """
    Main function to run the background check.
    
    Args:
        config: Configuration dictionary
    """
    print_banner()
    
    # Display configuration
    country_display = ", ".join([
        f"{code} ({get_country_name(code)})" 
        for code in config["flagged_countries"]
    ])
    print(f"\n[CONFIG] Flagged countries: {country_display}")
    print(f"[CONFIG] Max works to check: {config['max_works_to_check']}")
    print(f"[CONFIG] API delay: {config['api_delay']}s")
    
    headers = get_headers(config["user_agent"])
    
    # Read input file
    input_file = config["input_file"]
    print(f"\n[INFO] Reading file: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"[INFO] Loaded {len(df)} rows.")
    except FileNotFoundError:
        print(f"[ERROR] File '{input_file}' not found!")
        return
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return
    
    # Ensure OpenAlex IDs exist
    total_rows = len(df)
    df = ensure_openalex_ids(df, config, headers)
    
    # Filter candidates with OpenAlex ID
    has_id = df["OpenAlex_ID"].notna() & (df["OpenAlex_ID"] != "")
    candidates_df = df[has_id]
    candidates_with_id = len(candidates_df)
    skipped_count = total_rows - candidates_with_id
    
    print(f"[INFO] Total rows: {total_rows}")
    print(f"[INFO] With OpenAlex ID: {candidates_with_id}")
    if skipped_count > 0:
        print(f"[INFO] Skipped (no ID): {skipped_count}")
    
    if candidates_with_id == 0:
        print("[INFO] No candidates to process.")
        return
    
    # Initialize result columns
    df["Flag"] = "No"
    df["Affiliation_Type"] = "None"
    df["Flag_Evidence"] = ""
    
    # Process each candidate
    flagged_count = 0
    direct_count = 0
    indirect_count = 0
    flagged_candidates = []
    
    print(f"\n[INFO] Starting background check for {candidates_with_id} candidates...")
    print("-" * 70)
    
    for i, (df_index, row) in enumerate(candidates_df.iterrows()):
        try:
            is_flagged = process_candidate(
                df_index, row, df, candidates_with_id, config, headers, i + 1
            )
            
            if is_flagged:
                flagged_count += 1
                aff_type = df.at[df_index, "Affiliation_Type"]
                
                if aff_type == "Direct":
                    direct_count += 1
                else:
                    indirect_count += 1
                
                flagged_candidates.append({
                    "Name": f"{row['First Name']} {row['Last Name']}",
                    "Type": aff_type,
                    "Evidence": str(df.at[df_index, "Flag_Evidence"])[:100]
                })
                
        except KeyboardInterrupt:
            print("\n\n[INTERRUPTED] Process stopped by user.")
            print("[INFO] Saving progress...")
            break
        except Exception as e:
            print(f"    [ERROR] Failed to process: {e}")
            continue
    
    # Save results
    output_file = config["output_file"]
    
    # Change extension to xlsx for Excel output
    if output_file.endswith('.csv'):
        xlsx_file = output_file.replace('.csv', '.xlsx')
    else:
        xlsx_file = output_file + '.xlsx'
    
    print("\n" + "-" * 70)
    print(f"[INFO] Saving results to: {xlsx_file}")
    
    try:
        # Save to Excel with highlighting
        save_to_excel_with_highlight(df, xlsx_file)
        print("[SUCCESS] File saved successfully!")
        print(f"[INFO] Flagged rows are highlighted in YELLOW")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel: {e}")
        # Fallback to CSV
        print("[INFO] Falling back to CSV...")
        try:
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            print(f"[SUCCESS] CSV saved: {output_file}")
        except Exception as e2:
            print(f"[ERROR] Failed to save CSV: {e2}")
            return
    
    # Print summary
    clean_count = candidates_with_id - flagged_count
    print_summary(
        total_rows=total_rows,
        candidates_with_id=candidates_with_id,
        flagged_count=flagged_count,
        direct_count=direct_count,
        indirect_count=indirect_count,
        flagged_candidates=flagged_candidates,
        output_file=xlsx_file
    )


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check if countries were provided via command line
    if args.countries is None or len(args.countries) == 0:
        # No countries specified, show interactive menu
        selected_countries = interactive_country_selection()
    else:
        selected_countries = [c.upper() for c in args.countries]
    
    # Confirm selection
    country_names = [COUNTRY_NAMES.get(c, c) for c in selected_countries]
    print(f"\n[CONFIRMED] Checking affiliations with: {', '.join(country_names)}")
    
    # Build configuration from arguments
    config = get_config_from_args(args, selected_countries)
    
    run_background_check(config)


if __name__ == "__main__":
    main()
