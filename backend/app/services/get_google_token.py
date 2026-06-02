from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = Path(__file__).resolve().parent

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file(
    BASE_DIR / "client_secret.json",
    SCOPES
)

creds = flow.run_local_server(port=0)

print("\n=== TOKEN JSON ===\n")
print(creds.to_json())