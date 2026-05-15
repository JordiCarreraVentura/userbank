import os
import yaml
import re
from userbank import UserBank

# Configuration
CONFIG_FILE = "config.yml"
CREDENTIALS_PATH = "keys.json"

def get_spreadsheet_id():
    """
    Retrieves the spreadsheet ID from config.yml or prompts the user.
    """
    spreadsheet_id = None
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                # Load YAML content
                config = yaml.safe_load(f)
                url = None
                
                if isinstance(config, dict):
                    url = config.get('USER_BANK_URL')
                elif isinstance(config, str) and 'USER_BANK_URL=' in config:
                    # Handle edge case where YAML parses key=val as a string
                    url = config.split('USER_BANK_URL=')[1].strip()
                
                if url:
                    # Extract ID from URL using regex
                    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
                    if match:
                        spreadsheet_id = match.group(1)
            except Exception as e:
                # Fallback: manual parsing if YAML loader fails on key=val format
                f.seek(0)
                for line in f:
                    if 'USER_BANK_URL=' in line:
                        url = line.split('USER_BANK_URL=')[1].strip()
                        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
                        if match:
                            spreadsheet_id = match.group(1)
                            break

    if not spreadsheet_id:
        print("Spreadsheet ID not found in config.yml.")
        spreadsheet_id = input("Please enter the Spreadsheet ID: ").strip()
        
    return spreadsheet_id

def main():
    spreadsheet_id = get_spreadsheet_id()
    
    if not spreadsheet_id:
        print("Error: No Spreadsheet ID provided. Exiting.")
        return

    # 1. Initialize the UserBank
    bank = UserBank(
        spreadsheet_id=spreadsheet_id,
        credentials_path=CREDENTIALS_PATH
    )

    print(f"--- Using Spreadsheet ID: {spreadsheet_id} ---")

    print("\n--- Adding a user ---")
    try:
        new_user = bank.add_user(
            application="MyApp",
            email="john.doe@example.com",
            username="jdoe",
            password="securepassword123"
        )
        print(f"Added user: {new_user['UserName']}")
    except Exception as e:
        print(f"Error adding user: {e}")

    print("\n--- Searching for users (Exact match) ---")
    try:
        users = bank.search(application="MyApp", is_active=True)
        for u in users:
            print(f"Found: {u['UserName']} ({u['Email']})")
    except Exception as e:
        print(f"Error searching users: {e}")

    print("\n--- Searching for users (Regex match) ---")
    try:
        johns = bank.search(email_re="john.*")
        for u in johns:
            print(f"Found John: {u['UserName']} ({u['Email']})")
    except Exception as e:
        print(f"Error searching regex: {e}")

if __name__ == "__main__":
    main()
