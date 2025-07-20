# Demo Scripts and Files

This directory contains demonstration scripts and sample files for the TCGPlayer price history extraction application.

## Demo Scripts

### 1. `demo_price_extraction.py`
Demonstrates the core price history extraction functionality.

**Features:**
- Extracts price history tables from TCGPlayer markdown responses
- Parses structured data from the tables
- Generates normalized CSV output format
- Shows complete end-to-end extraction process

**Usage:**
```bash
cd demo
python3 demo_price_extraction.py
```

**Output:**
- `demo_normalized_output.csv` - Sample price history data in normalized format

### 2. `demo_idempotent.py`
Demonstrates the idempotent functionality of the application.

**Features:**
- Shows how the application prevents duplicate entries
- Runs the same input multiple times
- Demonstrates consistent output regardless of run count
- Perfect for testing automated/scheduled workflows

**Usage:**
```bash
cd demo
python3 demo_idempotent.py
```

**Output:**
- `demo_idempotent.csv` - Test file showing idempotent behavior
- Console output showing duplicate detection logs

## Sample Files

### Input Data
- `response_01.md` - Sample TCGPlayer product page response (Umbreon ex card)
  - Contains full HTML/markdown content from a real TCGPlayer page
  - Includes price history table with 30+ data points
  - Used by both demo scripts for testing

### Output Data
- `demo_normalized_output.csv` - Price history in normalized format
- `demo_idempotent.csv` - Output from idempotent testing
- `extracted_price_history.csv` - Sample extraction output
- `idempotent_test.csv` - Test data from idempotent functionality

## File Format

The normalized CSV format includes:
```csv
set,type,period,name,date,holofoil_price,additional_price
SV08.5,Card,3M,Umbreon ex 161,4/20 to 4/22,"$1,451.66",$0.00
```

**Fields:**
- `set`: Trading card set identifier (e.g., "SV08.5")
- `type`: Item type (e.g., "Card")
- `period`: Tracking period (e.g., "3M" for 3 months)
- `name`: Card/product name
- `date`: Price date range (e.g., "4/20 to 4/22")
- `holofoil_price`: Primary market price
- `additional_price`: Secondary/alternative price

## Running from Main Application

To process the demo data with the main application:

```bash
# From the app directory
PYTHONPATH=. pipenv run python3 main.py sample.csv demo/output.csv -v

# The application will:
# 1. Read the input CSV (sample.csv)
# 2. Fetch content from the TCGPlayer URL
# 3. Extract price history data
# 4. Generate normalized output in demo/output.csv
# 5. Prevent duplicates on subsequent runs (idempotent)
```

## Key Benefits Demonstrated

1. **Data Extraction**: Accurate parsing of TCGPlayer price tables
2. **Normalization**: Each price record becomes a separate row with metadata
3. **Idempotency**: Safe to run multiple times without data corruption
4. **Error Handling**: Graceful handling of missing files and malformed data
5. **Production Ready**: Comprehensive logging and status reporting

## Technical Notes

- Demo scripts use relative imports to access the common modules
- All file paths are adjusted for the demo directory structure
- Logging output is available in demo log files
- Sample data represents real TCGPlayer content for testing accuracy