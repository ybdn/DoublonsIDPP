# DoublonsIDPP - IDPP Duplicates Processing Script

**CRITICAL: Always follow these instructions first. Only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

DoublonsIDPP is a specialized Python data processing script for handling duplicate records in French law enforcement databases (IDPP - Identifiant Dactyloscopique de la Police et de la Gendarmerie). This script processes CSV files containing biometric signaling data to identify and eliminate duplicates based on complex business rules.

## Working Effectively

### Dependencies and Setup
- **NEVER CANCEL: Install dependencies with `pip3 install pandas numpy` - takes 15-30 seconds.**
- Python 3.12+ is required and available.
- The script uses pandas 2.3.1+ and numpy 2.3.2+ for data processing.
- No complex build process required - this is a standalone Python script.

### Running the Script
- **Always install dependencies first**: `pip3 install pandas numpy`
- **Run the main script**: `python3 script_doublons_idpp.py`
- **EXECUTION TIME**: Normal processing takes under 1 second for typical datasets (100-1000 records).
- **NEVER CANCEL**: For large datasets (10,000+ records), processing may take 5-30 seconds. Set timeout to 60+ seconds.

### Script Behavior
- The script runs interactively and prompts for:
  1. Input CSV file path (or automatically detects CSV files in current directory)
  2. Output directory for exports (defaults to `data/exports/`)
- Creates backup files automatically in `data/backups/`
- Generates multiple output files: detailed reports (CSV), simplified lists (CSV), and summaries (HTML/TXT)

## Validation

### Mandatory Validation Steps
**ALWAYS run these validation steps after making any changes:**

1. **Test Dependencies**:
   ```bash
   python3 -c "import pandas as pd, numpy as np; print('Dependencies OK')"
   ```

2. **Create Test Data**:
   ```bash
   cat > test_data.csv << 'EOF'
NUMERO_SIGNALISATION,NUMERO_PERSONNE,IDENTIFIANT_GASPARD,NOM,PRENOM,DATE_NAISSANCE_MIN,DATE_CREATION_FAED,NUM_PROCEDURE,NUMERO_CLICHE
12345,67890,GN123456789,DUPONT,PIERRE,01/01/1980,15/03/2024,00116/00149/2024,CLICHE001
67890,67890,GN123456789,DUPONT,PIERRE,01/01/1980,15/03/2024,00116/00149/2024,
54321,11111,PN987654321,MARTIN,JEAN,15/05/1975,20/03/2024,00200/00300/2024,CLICHE002
99999,22222,GN555666777,BERNARD,MARIE,25/12/1990,10/04/2024,00400/00500/2024,CLICHE003
EOF
   ```

3. **Test Core Functionality** (non-interactive):
   ```python
   python3 -c "
import script_doublons_idpp
import pandas as pd
df = script_doublons_idpp.lire_fichier_csv('test_data.csv')
assert df is not None and len(df) == 4
print('✓ Script validation passed')
"
   ```

4. **Manual Test Scenario**: 
   - Run the script with test data: `(echo "1"; echo "1") | python3 script_doublons_idpp.py`
   - **NEVER CANCEL**: This may take 10-30 seconds. Set timeout to 60+ seconds.
   - Verify output files are created in the `/home/runner/work/DoublonsIDPP/data/exports/[timestamp]/` directory
   - Check that HTML summary file opens correctly and shows processing statistics
   - **Expected output**: 4 files generated (conserved report, deletion report, simple list, HTML summary)

### Expected Validation Results
- Test data should identify 1 duplicate group (2 GN records with same identity)
- Should exclude 1 PN record automatically  
- Should generate 4 output files: conserved records, duplicates to delete, simple list, and HTML summary
- HTML summary should show processing statistics and file locations
- **Processing stats**: 3 total records (hors PN), 2 conserved (66.7%), 1 to delete (33.3%)
- **Output location**: Files created in `/home/runner/work/DoublonsIDPP/data/exports/[timestamp]/`

## Common Tasks

### Repository Structure
```
DoublonsIDPP/
├── .github/
│   └── copilot-instructions.md
├── README.md
├── script_doublons_idpp.py          # Main processing script
├── data/                            # Created at runtime
│   ├── backups/                     # Automatic backups
│   └── exports/                     # Output files by timestamp
```

### Key Script Functions
- `lire_fichier_csv()`: Loads and validates CSV input files
- `regrouper_doublons()`: Groups records by IDPP, person number, and identity
- `appliquer_tri_1/2/3()`: Applies hierarchical deduplication rules
- `generer_resultats()`: Creates output reports and summaries
- `filtrer_idpp_pn()`: Automatically excludes PN-prefixed records

### Input File Requirements
- **Required CSV columns**: NUMERO_SIGNALISATION, NUMERO_PERSONNE, IDENTIFIANT_GASPARD, NOM, PRENOM, DATE_NAISSANCE_MIN, DATE_CREATION_FAED, NUM_PROCEDURE, NUMERO_CLICHE
- **Encoding**: UTF-8
- **Format**: Standard CSV with comma separators
- **Sample data**: Use the validation test data above for testing

### Business Logic Rules
1. **Tri 1**: If NUMERO_SIGNALISATION = NUMERO_PERSONNE, keep that record
2. **Tri 2**: If UNA (from NUM_PROCEDURE) is contained in IDPP, keep that record  
3. **Tri 3**: Temporal criteria - keep oldest creation date, then records with photos, then lowest signaling number
4. **PN Exclusion**: Records with IDPP starting with 'PN' are automatically excluded

### Making Changes
- **Always backup**: Script automatically creates backups before processing
- **Test incrementally**: Use small CSV test files before processing large datasets
- **Validate outputs**: Always check the generated HTML summary for correctness
- **Performance**: Script handles thousands of records efficiently; no optimization needed for typical use cases
- **Cleanup**: Use `.gitignore` to exclude `__pycache__/`, `data/`, and temporary test files from commits

### Troubleshooting
- **"ModuleNotFoundError"**: Run `pip3 install pandas numpy`
- **"FileNotFoundError"**: Check CSV file path and ensure file exists
- **"KeyError" for columns**: Verify CSV has all required columns (see Input File Requirements)
- **Interactive prompts hang**: Use test data and validation scripts above instead of manual interaction
- **Permission errors**: Ensure write access to current directory for data/backups and data/exports folders

### Directory Creation
- Script automatically creates `data/backups/` and `data/exports/` directories
- Export files are organized by timestamp: `data/exports/YYYYMMDD_HHMM/`
- No manual directory setup required

## Performance Expectations
- **Dependency installation**: 15-30 seconds (NEVER CANCEL)
- **Small datasets** (< 100 records): Under 1 second
- **Medium datasets** (100-1000 records): 1-5 seconds  
- **Large datasets** (1000-10000 records): 5-30 seconds (NEVER CANCEL - set 60+ second timeout)
- **Very large datasets** (10000+ records): 30-120 seconds (NEVER CANCEL - set 180+ second timeout)

**CRITICAL TIMEOUT VALUES:**
- Use `timeout=60` for normal script execution
- Use `timeout=180` for large dataset processing  
- Use `timeout=30` for dependency installation
- **NEVER CANCEL** long-running operations - data processing can take time

Always run the validation steps above after making changes to ensure the script continues to work correctly with your modifications.