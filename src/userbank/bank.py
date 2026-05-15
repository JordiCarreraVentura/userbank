import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
from typing import Dict


def filter_passwords(user_dict: Dict) -> Dict:
    del user_dict["UserPassword"]
    return user_dict


class UserBank:
    """
    Official Google Sheets API client wrapper for User Management.
    Provides a Pythonic experience for adding and searching users.
    """
    
    FIELDS = [
        "Application", "Email", "UserName", "UserPassword", 
        "DateCreated", "DateLastAccess", "DateDeleted", "IsActive"
    ]
    
    def __init__(self, spreadsheet_id: str, credentials_path: Optional[str] = None, credentials_info: Optional[Dict] = None, sheet_name: str = "Sheet1"):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        if credentials_path:
            self.creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=self.scopes)
        elif credentials_info:
            self.creds = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=self.scopes)
        else:
            self.creds = self._load_credentials_from_env()
            
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet_api = self.service.spreadsheets()

    @classmethod
    def from_config(cls, config_path: str = "config.yml", credentials_path: Optional[str] = None, credentials_info: Optional[Dict] = None, sheet_name: str = "Sheet1"):
        """
        Factory method to create a UserBank instance from a YAML configuration file.
        Extracts the Spreadsheet ID from USER_BANK_URL.
        """
        import yaml # Delayed import
        
        spreadsheet_id = None
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    url = None
                    if isinstance(config, dict):
                        url = config.get('USER_BANK_URL')
                    
                    if url:
                        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
                        if match:
                            spreadsheet_id = match.group(1)
                except Exception:
                    # Fallback for simple key=val format
                    f.seek(0)
                    for line in f:
                        if 'USER_BANK_URL=' in line:
                            url = line.split('USER_BANK_URL=')[1].strip()
                            match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
                            if match:
                                spreadsheet_id = match.group(1)
                                break
        
        if not spreadsheet_id:
            spreadsheet_id = input(f"Spreadsheet ID not found in {config_path}. Please enter it: ").strip()
            
        return cls(spreadsheet_id=spreadsheet_id, credentials_path=credentials_path, credentials_info=credentials_info, sheet_name=sheet_name)

    def initialize_sheet(self):
        """
        Ensures the sheet has the correct header row.
        """
        values = self._get_raw_values(f"{self.sheet_name}!A1:H1")
        if not values or values[0] != self.FIELDS:
            body = {'values': [self.FIELDS]}
            self.sheet_api.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.sheet_name}!A1:H1",
                valueInputOption="RAW",
                body=body
            ).execute()

    @staticmethod
    def _load_credentials_from_env():
        load_dotenv()

        path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if path and os.path.exists(path):
            return service_account.Credentials.from_service_account_file(
                path, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )

        json_str = os.environ.get("USER_BANK_CREDENTIALS_JSON")
        if json_str:
            info = json.loads(json_str)
            return service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )

        raise ValueError(
            "No credentials found. Provide 'credentials_path' or 'credentials_info', "
            "or set GOOGLE_APPLICATION_CREDENTIALS / USER_BANK_CREDENTIALS_JSON in the environment or .env file."
        )

    def _get_raw_values(self, range_name: Optional[str] = None) -> List[List[str]]:
        """Fetch values from the sheet."""
        if not range_name:
            range_name = f"{self.sheet_name}!A:H"
        
        result = self.sheet_api.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])

    def add_user(self, application: str, email: str, username: str, password: str, is_active: bool = True) -> Dict[str, str]:
        """
        Add a user programmatically.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            application,
            email,
            username,
            password,
            now,        # DateCreated
            now,        # DateLastAccess
            "",         # DateDeleted
            "TRUE" if is_active else "FALSE"
        ]
        
        body = {'values': [row]}
        self.sheet_api.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!A:H",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        return dict(zip(self.FIELDS, row))

    def search(self, **kwargs) -> List[Dict[str, str]]:
        """
        Search users by any combination of criteria.
        
        Supported kwargs:
        - Exact match: Use field names (e.g., Application="App1", Email="test@ex.com")
        - Regex match: Append '_re' to field names (e.g., UserName_re="admin.*", Application_re="^Dev")
        - Boolean: 'is_active' (True/False)
        """
        all_values = self._get_raw_values()
        if not all_values or len(all_values) < 1:
            return []
            
        header = all_values[0]
        rows = all_values[1:]
        
        col_idx = {name.lower(): i for i, name in enumerate(header)}
        
        results = []
        for row in rows:
            row = row + [""] * (len(header) - len(row))
            user_dict = dict(zip(header, row))
            
            match = True
            for key, criterion in kwargs.items():
                if criterion is None: continue
                
                if key.lower() == "is_active":
                    val = user_dict.get("IsActive", "").upper() == "TRUE"
                    if val != criterion:
                        match = False
                        break
                    continue

                is_re = key.lower().endswith("_re")
                field_key = key[:-3].lower() if is_re else key.lower()
                
                target_idx = col_idx.get(field_key)
                if target_idx is None: continue 

                target_val = row[target_idx]
                
                if is_re:
                    if not re.search(str(criterion), target_val, re.IGNORECASE):
                        match = False
                        break
                else:
                    if str(target_val).lower() != str(criterion).lower():
                        match = False
                        break
            
            if match:
                results.append(filter_passwords(user_dict))
                
        return results
