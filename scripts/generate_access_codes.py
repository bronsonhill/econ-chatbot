import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime
import logging
import hashlib
import uuid
import string
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_mongo_client(connection_string):
    return MongoClient(connection_string, server_api=ServerApi('1'))

def generate_access_code(prefix="RABBIT", length=5):
    """Generate a random access code with prefix."""
    # Generate random alphanumeric string
    characters = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(characters, k=length))
    return f"{prefix}{random_part}"

def generate_access_codes_from_csv(input_csv_path, connection_string, code_prefix="RABBIT"):
    """
    1. Read student/user data from CSV
    2. Generate access codes
    3. Save new CSV with access codes
    4. Upload access codes to MongoDB
    """
    try:
        # Read CSV file
        df = pd.read_csv(input_csv_path)
        
        # Generate access codes for each row
        df['access_code'] = [generate_access_code(code_prefix) for _ in range(len(df))]
        
        # Save new CSV with access codes
        output_path = input_csv_path.rsplit('.', 1)[0] + '_with_access_codes.csv'
        df.to_csv(output_path, index=False)
        logging.info(f"Saved CSV with access codes to: {output_path}")

        # Connect to MongoDB and upload access codes
        client = get_mongo_client(connection_string)
        db = client.rabbitbot
        collection = db.valid_identifiers

        # Clear existing access codes if needed
        should_clear = input("Clear existing access codes? (y/n): ").lower() == 'y'
        if should_clear:
            collection.delete_many({})
            logging.info("Cleared existing access codes")

        # Prepare documents (only access codes, no personal data)
        documents = [
            {
                "identifier": access_code,
                "created_at": datetime.utcnow(),
                "type": "rabbit_study"
            }
            for access_code in df['access_code'].unique()
        ]

        # Insert documents
        if documents:
            collection.insert_many(documents)
            logging.info(f"Successfully loaded {len(documents)} access codes into MongoDB")
            
            # Print example mappings for verification
            logging.info("\nExample access code mappings (first 5):")
            for _, row in df.head().iterrows():
                logging.info(f"User -> Access Code: {row['access_code']}")
        else:
            logging.warning("No valid access codes generated")

    except Exception as e:
        logging.error(f"Error processing access codes: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()

def generate_bulk_access_codes(num_codes, connection_string, code_prefix=""):
    """
    Generate a specified number of access codes and upload to MongoDB.
    """
    try:
        # Generate access codes
        access_codes = [generate_access_code(code_prefix) for _ in range(num_codes)]
        
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
        documents = [
            {
                "identifier": access_code,
                "created_at": datetime.utcnow(),
                "type": "rabbit_study"
            }
            for access_code in access_codes
        ]

        # Insert documents
        if documents:
            collection.insert_many(documents)
            logging.info(f"Successfully loaded {len(documents)} access codes into MongoDB")
            
            # Save to CSV for distribution
            df = pd.DataFrame({'access_code': access_codes})
            output_path = f"rabbit_access_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_path, index=False)
            logging.info(f"Saved access codes to: {output_path}")
            
            # Print first few codes for verification
            logging.info("\nFirst 5 access codes:")
            for code in access_codes[:5]:
                logging.info(f"  {code}")
        else:
            logging.warning("No access codes generated")

    except Exception as e:
        logging.error(f"Error generating access codes: {str(e)}")
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
    print("1. Generate access codes from CSV file")
    print("2. Generate bulk access codes")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        csv_path = input("Enter path to CSV file containing user information: ").strip()
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        generate_access_codes_from_csv(csv_path, connection_string)
    
    elif choice == "2":
        num_codes = int(input("Enter number of access codes to generate: "))
        generate_bulk_access_codes(num_codes, connection_string)
    
    else:
        print("Invalid choice. Exiting.")
