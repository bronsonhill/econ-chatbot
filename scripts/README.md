# Access Code Management Scripts

These scripts help you manage access codes for the Rabbit chatbot application.

## Scripts

### 1. `generate_access_codes.py`
Generates access codes for the Rabbit chatbot.

**Options:**
- **From CSV**: Generate access codes from a CSV file containing user information
- **Bulk Generation**: Generate a specified number of random access codes

**Usage:**
```bash
python scripts/generate_access_codes.py
```

**Features:**
- Generates codes with format: `RABBIT` + 8 random alphanumeric characters
- Saves generated codes to CSV for distribution
- Uploads codes to MongoDB database
- Option to clear existing codes

### 2. `load_access_codes.py`
Manages existing access codes in the database.

**Options:**
- **Load from CSV**: Load access codes from a CSV file
- **List codes**: View all access codes in the database
- **Delete codes**: Remove all access codes from the database

**Usage:**
```bash
python scripts/load_access_codes.py
```

## CSV Format

For loading access codes from CSV, the file should have one of these column names:
- `access_code`: Contains the access codes
- `identifier`: Alternative column name for access codes

Example CSV:
```csv
access_code
RABBIT12345678
RABBIT87654321
RABBITABCDEFGH
```

## Database Structure

Access codes are stored in MongoDB with the following structure:
```json
{
  "identifier": "RABBIT12345678",
  "created_at": "2024-01-01T00:00:00Z",
  "type": "rabbit_study"
}
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install pandas pymongo python-dotenv toml
   ```

2. **Configure connection:**
   - Set `MONGODB_CONNECTION_STRING` environment variable, or
   - The scripts will read from `.streamlit/secrets.toml` automatically

3. **Run scripts:**
   ```bash
   python scripts/generate_access_codes.py
   python scripts/load_access_codes.py
   ```

## Example Workflows

### Generate 50 access codes for a class:
```bash
python scripts/generate_access_codes.py
# Choose option 2
# Enter 50
# Choose y to clear existing codes
```

### Load access codes from a CSV file:
```bash
python scripts/load_access_codes.py
# Choose option 1
# Enter path to CSV file
# Choose y/n for clearing existing codes
```

### Check what access codes exist:
```bash
python scripts/load_access_codes.py
# Choose option 2
```

## Security Notes

- Access codes are stored in MongoDB with timestamps
- The scripts can clear all existing codes (use with caution)
- Generated codes are random and hard to guess
- Consider rotating access codes periodically for security
