import os
import requests
import yaml
import sys
from dotenv import load_dotenv

# --- Configuration & Constants ---
BASE_AUTH_URL = "https://auth.apps.paloaltonetworks.com/auth/v1/oauth2/access_token"
EXCLUSION_URL = "https://api.sase.paloaltonetworks.com/sse/config/v1/decryption-exclusions"
MS_ENDPOINT_URL = "https://endpoints.office.com/endpoints/worldwide?clientrequestid=b10c5ed1-bad1-445f-b386-b919946339a7"
INPUT_FILE = "exclusions.yaml"

HEADERS = {"Accept": "application/json"}
AUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
}

load_dotenv()
TSG_ID = os.environ.get("TSG_ID")
CLIENT_ID = os.environ.get("CLIENT_ID")
SECRET_ID = os.environ.get("SECRET_ID")

# --- Microsoft Data Functions ---

def get_microsoft_fqdns():
    """Fetches 'Allow' and 'Optimize' FQDNs from Microsoft."""
    try:
        print(f"[*] Fetching endpoints from Microsoft...")
        response = requests.get(MS_ENDPOINT_URL)
        response.raise_for_status()
        data = response.json()

        fqdns = set()
        for item in data:
            if item.get('category') in ['Allow', 'Optimize']:
                for url in item.get('urls', []):
                    fqdns.add(url)
        
        return sorted(list(fqdns))
    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching Microsoft data: {e}", file=sys.stderr)
        return []

def update_yaml_file(fqdns):
    """Writes the retrieved FQDNs into the exclusions.yaml file."""
    yaml_data = {"exclusions": []}
    for fqdn in fqdns:
        yaml_data["exclusions"].append({
            "domain": fqdn,
            "reason": "Microsoft 365 Optimized Endpoint"
        })
    
    with open(INPUT_FILE, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
    print(f"\n[+] SUCCESS: {INPUT_FILE} has been updated with {len(fqdns)} domains.")

# --- Prisma Access Functions ---

def create_token():
    """Authenticates and updates the global HEADERS with a Bearer token."""
    auth_params = f"grant_type=client_credentials&scope:tsg_id:{TSG_ID}"
    auth_url = f"{BASE_AUTH_URL}?{auth_params}"

    response = requests.post(
        url=auth_url,
        headers=AUTH_HEADERS,
        auth=(CLIENT_ID, SECRET_ID),
    )
    response.raise_for_status()
    token_data = response.json()
    HEADERS.update({"Authorization": f'Bearer {token_data["access_token"]}'})

def update_decryption_exclusion(domain, description):
    """Sends a POST request to Prisma Access to add a domain exclusion."""
    payload = {"name": domain, "description": description}
    params = {"tsg_id": TSG_ID, "folder": "Shared"}

    response = requests.post(
        EXCLUSION_URL, headers=HEADERS, params=params, json=payload
    )
    if response.status_code == 201:
        print(f"  [+] Added: {domain}")
    else:
        # Handling existing domains or errors
        print(f"  [-] Skip/Fail {domain}: {response.status_code}")

# --- Main Execution Flow ---

if __name__ == "__main__":
    # 1. Fetch from Microsoft
    fqdns = get_microsoft_fqdns()
    
    if not fqdns:
        print("[!] No domains found. Exiting.")
        sys.exit(1)

    # 2. Populate the local YAML file
    update_yaml_file(fqdns)

    # 3. THE STOP: Manual Verification
    print("\n" + "="*50)
    print("ACTION REQUIRED: PLEASE VERIFY THE LIST")
    print(f"Open '{INPUT_FILE}' in your editor and check the domains.")
    print("="*50)
    
    user_input = input("\nPress [ENTER] to continue with the Prisma API upload, or type 'quit' to exit: ")
    
    if user_input.lower() == 'quit':
        print("Exiting without making changes to Prisma Access.")
        sys.exit(0)

    # 4. Authenticate and Push to Prisma
    print("\n[*] Starting Prisma Access API calls...")
    try:
        create_token()
        with open(INPUT_FILE, "r") as f:
            data = yaml.safe_load(f)
        
        items = data.get("exclusions", [])
        for item in items:
            domain = item.get("domain")
            reason = item.get("reason", "Automation Added")
            if domain:
                update_decryption_exclusion(domain, reason)
        
        print("\n[+] Process Complete.")
        
    except Exception as e:
        print(f"[!] Critical Error during Prisma update: {e}")
        sys.exit(1)