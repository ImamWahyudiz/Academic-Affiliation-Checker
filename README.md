# Academic Affiliation Background Checker

A Python tool for checking academic researchers' affiliations with specified countries using OpenAlex API. Performs both direct affiliation checks (author's own institutions) and indirect checks (co-authors' institutions).

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![OpenAlex](https://img.shields.io/badge/API-OpenAlex-orange.svg)

## Features

- **Direct Affiliation Check**: Checks author's employment/affiliation history
- **Indirect Affiliation Check**: Checks co-authors' institutions from recent publications
- **False Positive Prevention**: Filters out generic institution names that often have incorrect country tags
- **Interactive Mode**: Select countries to check via menu
- **Flexible Configuration**: Command line arguments for all options
- **Detailed Evidence**: Shows institution names, years, and co-author details

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/affiliation-checker.git
cd affiliation-checker

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Requirements

```
pandas>=1.5.0
requests>=2.28.0
openpyxl>=3.0.0
```

## How It Works

The system performs a **2-step verification** for each candidate:

| Step | Check Type | Data Source | Description |
|------|------------|-------------|-------------|
| 1 | **Direct Affiliation** | Author Profile | Checks author's own affiliation history from OpenAlex profile |
| 2 | **Indirect Affiliation** | Recent Publications | Checks co-authors' institutions from recent works/papers |

### Step 1: Direct Affiliation Check
- Retrieves author profile from OpenAlex API
- Checks `affiliations` array (full employment history with years)
- Checks `last_known_institutions` (current/recent affiliations)
- If any institution's country matches flagged countries → **FLAGGED as Direct**

### Step 2: Indirect Affiliation Check
*(only runs if Step 1 is clean)*
- Fetches author's recent publications (configurable via `--works`)
- For each publication, checks all co-authors' institutions
- If any co-author is affiliated with flagged country → **FLAGGED as Indirect**
- Evidence includes: co-author name, institution, country, publication year

## ⚠️ Important: Manual Verification Required

> **This tool is a screening aid, NOT a definitive assessment.**
> 
> **Always manually verify flagged results**, especially for **Direct affiliations**.

### Why Manual Verification is Critical

OpenAlex builds affiliation data from publication metadata, which can be **inaccurate or misleading**:

| Scenario | What OpenAlex Shows | Reality |
|----------|---------------------|---------|
| Co-authored paper | Author affiliated with foreign institution for 1 year | Collaboration/visiting, not employment |
| Dual affiliation paper | Multiple institution affiliations | Author only works at one, listed both on paper |
| Data entry error | Wrong institution tagged | Publisher/metadata error |
| Name collision | Mixed data from different people | Similar names merged incorrectly |

### Real Example

```
Willy Susilo (University of Wollongong, Australia)
├── OpenAlex shows: "Sharif University of Technology [Iran] (2014)"
├── Reality: Likely a single collaborative paper, not employment
└── Action needed: Verify if actual affiliation or just collaboration
```

### Verification Checklist

When a candidate is flagged, verify manually:

1. **For Direct Affiliations:**
   - [ ] Check the candidate's CV/LinkedIn for actual employment history
   - [ ] Look up the specific publication(s) from that institution
   - [ ] Determine if it was employment vs. short-term visit/collaboration
   - [ ] Contact the candidate if needed for clarification

2. **For Indirect (Co-author) Affiliations:**
   - [ ] Review the publication context (conference, journal)
   - [ ] Assess if the collaboration is ongoing or one-time
   - [ ] Consider the nature of the research relationship

### Understanding Affiliation Years

- **Multiple years (e.g., 2015-2024)**: Likely actual employment
- **Single year (e.g., 2014)**: Could be just one paper/collaboration
- **Recent single year**: More concerning than old single year

## Usage

```bash
# Interactive mode (will prompt for country selection)
python affiliation_checker.py

# Interactive mode with custom input file
python affiliation_checker.py -i Data.csv

# Direct mode (skip interactive menu)
python affiliation_checker.py -i Data.csv -c IL IR RU

# Full options
python affiliation_checker.py -i candidates.csv -o results.csv -c IL IR RU --works 50 --delay 0.3
```

### Interactive Mode

When running without `-c` flag, program displays country selection menu:

```
======================================================================
SELECT COUNTRIES TO CHECK FOR AFFILIATIONS
======================================================================
  IL=Israel        IR=Iran          RU=Russia        CN=China
  KP=North Korea   SY=Syria         CU=Cuba          BY=Belarus
  ...
----------------------------------------------------------------------
Input: kode negara dipisah spasi, contoh: IL IR RU
----------------------------------------------------------------------
>>> _
```

### Command Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `-i, --input` | Input CSV file | `Data.csv` |
| `-o, --output` | Output CSV file | `Vetted_Output.csv` |
| `-c, --countries` | Country codes to flag (ISO 3166-1 alpha-2). If omitted, shows interactive menu | - |
| `--works` | Max works to check for indirect affiliations | `30` |
| `--delay` | Delay between API requests (seconds) | `0.2` |
| `--email` | Email for API polite pool | - |

### Country Codes

| Code | Country |
|------|---------|
| IL | Israel |
| IR | Iran |
| RU | Russia |
| CN | China |
| KP | North Korea |
| SY | Syria |
| CU | Cuba |

## Input CSV Format

Your input CSV should have these columns:

```csv
First Name,Last Name,OpenAlex_ID
```

If `OpenAlex_ID` is missing, the program will automatically search for authors.

## Output Format

Output is saved as **Excel (.xlsx)** with:
- **Yellow highlighting** for flagged rows
- Frozen header row
- Auto-adjusted column widths

### Output Columns

| Column | Description |
|--------|-------------|
| Flag | `Yes` or `No` |
| Affiliation_Type | `Direct`, `Indirect (Co-author)`, or `None` |
| Flag_Evidence | Details of flagged affiliations |

### Example Output

```
[25/50] Checking: John Doe
    OpenAlex ID: A5012345678
    [STEP 1] Checking direct affiliations...
    [OK] No direct affiliation found
    [STEP 2] Checking indirect affiliations (last 30 works)...
    Found 30 works to check
    [FLAG] INDIRECT affiliation found through co-authors!
           - Co-author: Jane Smith at Tel Aviv University [Israel] (2024)
```

## False Positive Prevention

OpenAlex API sometimes returns incorrect country codes for generic institutions. For example, "Ministry of Education" exists in many countries, but may be incorrectly tagged with a specific country code.

To prevent false positives, the following institution name patterns are automatically **excluded** from checks:

| Pattern | Reason |
|---------|--------|
| Ministry of Education | Exists in many countries, often incorrectly tagged |
| Ministry of Science | Generic governmental body |
| Ministry of Health | Generic governmental body |
| Ministry of... | Any ministry-related institution |
| Department of Education | Generic governmental body |
| National Science Foundation | May have incorrect country tags |
| Government of... | Generic governmental reference |
| State Council | Generic governmental body |

This filter significantly reduces false positives while maintaining accuracy for legitimate academic institutions.

### Author Name Verification

The system also verifies that the OpenAlex author name matches the expected candidate name. This prevents false positives from **ID mismatches** where different authors with similar names get confused.

**Example Issue:**
- Input: "Liang Jiang" (quantum computing researcher at University of Chicago)
- OpenAlex ID returns: "Hualiang Jiang" (medicinal chemistry researcher in China)
- Result: **Name mismatch detected → Check skipped**

When a mismatch is detected, the output shows:
```
[X/Y] Checking: Liang Jiang
    OpenAlex ID: A5001392142
    [WARNING] Name mismatch! Expected: 'Liang Jiang', Got: 'Hualiang Jiang'
    [SKIP] Skipping affiliation check due to potential ID mismatch
```

The flag evidence column will show: `ID Mismatch: OpenAlex shows 'Hualiang Jiang'`

### Institution Verification

When your input data includes a **"Current Institution"** column, the system performs additional verification:

1. **Name + Institution Match**: Both name AND institution must be found in OpenAlex history → High confidence
2. **Name Match Only**: Name matches but institution not found → Allowed with warning (data might be outdated)
3. **Name Mismatch**: Different name even if institution matches → Rejected (different person)

This helps distinguish between multiple people with similar names:

| Input | OpenAlex Shows | Institution Check | Result |
|-------|----------------|-------------------|--------|
| Liang Jiang @ U. Chicago | Hualiang Jiang | No match | ❌ REJECTED |
| John Smith @ MIT | John Smith | MIT found in history | ✅ VERIFIED |
| Robert Wille @ TU Munich | Robert Wille | TUM found in history | ✅ VERIFIED |

**Note**: Institution matching uses keyword comparison, so variations like "Technical University of Munich" and "TU München" are treated as matches.

## Examples

### Interactive country selection
```bash
python affiliation_checker.py -i Data.csv
# Then enter: IL IR RU
```

### Direct mode (skip menu)
```bash
python affiliation_checker.py -i Data.csv -c IL IR RU CN
```

### Slower API calls (avoid rate limiting)
```bash
python affiliation_checker.py -i Data.csv -c IL IR --delay 1.0 --works 10
```

### Use polite API pool (faster)
```bash
python affiliation_checker.py -i Data.csv -c IL IR --email your@email.com
```

## API Information

### OpenAlex API
- **Free**: No API key required
- **Rate Limit**: 100,000 requests/day
- **Polite Pool**: Add email to User-Agent for faster limits
- **Documentation**: https://docs.openalex.org/

## Troubleshooting

### ModuleNotFoundError
```bash
pip install pandas requests
```

### API Rate Limiting
- Add `--delay 0.5` to slow down requests
- Add `--email your@email.com` to use OpenAlex polite pool

### No Results Found
- Check that input CSV has correct headers
- Verify "First Name" and "Last Name" columns exist
- Try with fewer candidates first

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **IMPORTANT**: This tool is provided for **screening purposes only**. 

- The accuracy of results depends entirely on OpenAlex database quality
- **Direct affiliations may reflect collaborations, not actual employment**
- A single-year affiliation often means just one collaborative paper
- **Always verify flagged candidates manually before making any decisions**
- The authors are not responsible for decisions made based on this tool's output

**Do NOT use this tool as the sole basis for any personnel, hiring, or security decisions.**

## Acknowledgments

- [OpenAlex](https://openalex.org/) - Free and open academic database
