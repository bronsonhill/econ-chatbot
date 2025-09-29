import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_mongo_client(connection_string):
    return MongoClient(connection_string, server_api=ServerApi('1'))

def load_access_codes(csv_path, connection_string):
    """
    Load access codes from CSV file into MongoDB.
    Expected CSV format: Must have a column named 'access_code' or 'identifier'
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Check for access code column
        if 'access_code' in df.columns:
            code_column = 'access_code'
        elif 'identifier' in df.columns:
            code_column = 'identifier'
        else:
            raise ValueError("CSV must contain 'access_code' or 'identifier' column")

        # Connect to MongoDB
        client = get_mongo_client(connection_string)
        db = client.rabbitbot
        collection = db.valid_identifiers

        # Clear existing access codes if needed
        should_clear = input("Clear existing access codes? (y/n): ").lower() == 'y'
        if should_clear:
            collection.delete_many({})
            logging.info("Cleared existing access codes")

        # Prepare documents
        documents = []
        for access_code in df[code_column].unique():
            if pd.notna(access_code):  # Skip empty/NaN values
                documents.append({
                    "identifier": str(access_code).strip(),
                    "created_at": datetime.utcnow(),
                    "type": "rabbit_study"
                })

        # Insert documents
        if documents:
            collection.insert_many(documents)
            logging.info(f"Successfully loaded {len(documents)} access codes")
            
            # Print first few codes for verification
            logging.info("\nFirst 5 access codes loaded:")
            for code in df[code_column].head():
                logging.info(f"  {code}")
        else:
            logging.warning("No valid access codes found in CSV")

    except Exception as e:
        logging.error(f"Error loading access codes: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()

def list_access_codes(connection_string):
    """List all access codes in the database."""
    try:
        client = get_mongo_client(connection_string)
        db = client.rabbitbot
        collection = db.valid_identifiers

        # Get all access codes
        codes = list(collection.find({}, {"identifier": 1, "created_at": 1, "type": 1}))
        
        if codes:
            logging.info(f"Found {len(codes)} access codes:")
            for code in codes:
                logging.info(f"  {code['identifier']} (created: {code.get('created_at', 'unknown')})")
        else:
            logging.info("No access codes found in database")

    except Exception as e:
        logging.error(f"Error listing access codes: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()

def delete_access_codes(connection_string):
    """Delete all access codes from the database."""
    try:
        client = get_mongo_client(connection_string)
        db = client.rabbitbot
        collection = db.valid_identifiers

        # Confirm deletion
        confirm = input("Are you sure you want to delete ALL access codes? (yes/no): ").lower()
        if confirm == 'yes':
            result = collection.delete_many({})
            logging.info(f"Deleted {result.deleted_count} access codes")
        else:
            logging.info("Deletion cancelled")

    except Exception as e:
        logging.error(f"Error deleting access codes: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    # Get MongoDB connection string from environment or secrets
    connection_string = os.getenv("MONGODB_CONNECTION_STRING")
    if not connection_string:
        # Try to read from secrets.toml
        try:
            import toml
            secrets = toml.load(".streamlit/secrets.toml")
            connection_string = secrets.get("MONGODB_CONNECTION_STRING")
        except:
            pass
    
    if not connection_string:
        connection_string = input("Enter MongoDB connection string: ").strip()
    
    if not connection_string:
        raise ValueError("MongoDB connection string is required")

    print("Choose an option:")
    print("1. Load access codes from CSV file")
    print("2. List all access codes")
    print("3. Delete all access codes")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        csv_path = input("Enter path to CSV file: ").strip()
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        load_access_codes(csv_path, connection_string)
    
    elif choice == "2":
        list_access_codes(connection_string)
    
    elif choice == "3":
        delete_access_codes(connection_string)
    
    else:
        print("Invalid choice. Exiting.")
