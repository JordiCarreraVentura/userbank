import json
import os
import re
import shutil
import sys
from pathlib import Path


def _prompt(question, default=None):
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default or ""


def _confirm(question, default=True):
    suffix = " [Y/n]" if default else " [y/N]"
    answer = input(f"{question}{suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def _write_dotenv(keys_path):
    dotenv_path = Path(".env")
    lines = []
    if dotenv_path.exists():
        lines = dotenv_path.read_text().splitlines()
    new_lines = []
    written = False
    for line in lines:
        if line.startswith("GOOGLE_APPLICATION_CREDENTIALS="):
            new_lines.append(f"GOOGLE_APPLICATION_CREDENTIALS={keys_path}")
            written = True
        else:
            new_lines.append(line)
    if not written:
        new_lines.append(f"GOOGLE_APPLICATION_CREDENTIALS={keys_path}")
    dotenv_path.write_text("\n".join(new_lines) + "\n")


def main():
    print("=" * 60)
    print("  UserBank Setup")
    print("  Google Sheets credential wizard")
    print("=" * 60)
    print()

    # --- Phase 1: Service Account ---
    print("1) Google Service Account")
    print()
    print("   UserBank needs a service account to access your spreadsheet")
    print("   without manual login. If you already have a JSON key file,")
    print("   have the path ready.")
    print()
    print("   To create one:")
    print("     a) Go to https://console.cloud.google.com/apis/credentials")
    print("     b) Select/create a project, enable Google Sheets API")
    print("     c) Create Service Account → Keys → Add Key → New Key (JSON)")
    print()

    keys_path = "keys.json"

    if os.path.exists(keys_path):
        with open(keys_path) as f:
            info = json.load(f)
        client_email = info.get("client_email", "?")
        print(f"   ✔  Found {keys_path}")
        print(f"      Service account: {client_email}")
    else:
        choice = _prompt("   Enter path to JSON key file (or paste JSON content)")
        if choice.startswith("{"):
            try:
                info = json.loads(choice)
                with open(keys_path, "w") as f:
                    json.dump(info, f, indent=2)
                client_email = info.get("client_email", "?")
                print(f"   ✔  Saved to {keys_path}")
                print(f"      Service account: {client_email}")
            except json.JSONDecodeError:
                print("   ✖  Invalid JSON. Aborting.")
                sys.exit(1)
        else:
            src = Path(choice).expanduser().resolve()
            if not src.exists():
                print(f"   ✖  File not found: {src}")
                sys.exit(1)
            try:
                with open(src) as f:
                    info = json.load(f)
                client_email = info.get("client_email", "?")
                shutil.copy2(str(src), keys_path)
                print(f"   ✔  Copied to {keys_path}")
                print(f"      Service account: {client_email}")
            except (json.JSONDecodeError, OSError) as e:
                print(f"   ✖  Error: {e}")
                sys.exit(1)

    print()

    # --- Phase 2: Enable API ---
    print("2) Enable Google Sheets API")
    print()
    print("   Go to the URL below and click Enable:")
    print("   https://console.cloud.google.com/apis/api/sheets.googleapis.com/")
    print("   (It may be already enabled — skip if so.)")
    print()

    # --- Phase 3: Spreadsheet ---
    print("3) Google Spreadsheet")
    print()
    print("   Create or open a Google Sheet and share it with:")
    print(f"      {client_email}")
    print("   (Share → paste that email → Editor → Send)")
    print()

    config_url = None
    if os.path.exists("config.yml"):
        try:
            import yaml
            with open("config.yml") as f:
                cfg = yaml.safe_load(f)
            if isinstance(cfg, dict):
                config_url = cfg.get("USER_BANK_URL")
                if config_url:
                    print(f"   ✔  Found in config.yml: {config_url}")
        except Exception:
            pass

    if not config_url:
        config_url = _prompt("   Paste your spreadsheet URL")
        if config_url:
            with open("config.yml", "w") as f:
                f.write(f"USER_BANK_URL={config_url}\n")
            print("   ✔  Saved to config.yml")

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", config_url) if config_url else None
    if not match:
        print("   ✖  Could not extract spreadsheet ID from the URL.")
        print("      Expected: https://docs.google.com/spreadsheets/d/...")
        sys.exit(1)
    spreadsheet_id = match.group(1)
    print(f"      Spreadsheet ID: {spreadsheet_id}")
    print()

    # --- Phase 4: .env ---
    print("4) Environment")
    _write_dotenv(keys_path)
    print(f"   ✔  Wrote GOOGLE_APPLICATION_CREDENTIALS={keys_path} to .env")
    print()

    # --- Phase 5: Connection test ---
    print("5) Connection Test")
    if _confirm("   Attempt to verify the setup?"):
        try:
            from userbank import UserBank
            bank = UserBank(spreadsheet_id=spreadsheet_id, credentials_path=keys_path)
            bank._get_raw_values()
            print("   ✔  Connected! Your spreadsheet is accessible.")
        except Exception as e:
            print(f"   ✖  Connection failed: {e}")
            print()
            print("   Common fixes:")
            print(f"   - Share the sheet with {client_email}")
            print("   - Enable Google Sheets API in your Cloud project")
    else:
        print("   Skipped.")

    print()
    print("   ─────────────────────────────────────────────")
    print("   Done. Quickstart:")
    print()
    print("     from userbank import UserBank")
    print("     bank = UserBank.from_config()")
    print("     bank.initialize_sheet()")
    print("     bank.add_user('MyApp', 'a@b.com', 'user', 'pass')")
    print()
