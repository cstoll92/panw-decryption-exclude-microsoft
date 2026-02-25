# M365 to Prisma Access: Decryption Exclusion Automation

This tool automates the retrieval of Microsoft 365 "Optimize" and "Allow" endpoints and pushes them to **Palo Alto Networks Prisma Access** as decryption exclusions. It includes a built-in verification step to ensure you can review the domain list before any API calls are made to your security infrastructure.

## Features
* **Automatic Fetching:** Queries the Microsoft 365 Endpoint API for the latest worldwide FQDNs.
* **Smart Filtering:** Only includes domains categorized as `Optimize` or `Allow`.
* **Local Staging:** Generates a local `exclusions.yaml` file for auditing.
* **Human-in-the-loop:** Pauses execution after generating the list, allowing for manual review/editing.
* **Prisma Integration:** Automatically handles OAuth2 authentication and POSTs exclusions to the SASE tenant.

---

## Prerequisites

1.  **Python 3.x** installed.
2.  **Prisma Access Service Account:** You need a Service Account with "Super Admin" or "Network Administrator" permissions.

## Installation
Clone the repository:

```git clone https://github.com/cstoll92/panw-decryption-exclude-microsoft.git```

**Install the dependencies** using pip install -r requirements.txt
**Rename .env.example to .env** and populate your variables in this file generated while creating the service account. The .env is included in the .gitignore to ensure it does not accidentally get checked into a git repo.

## Usage
Run the script from your terminal:

Bash
python main.py

### The Workflow:
Fetch: The script pulls FQDNs from Microsoft.

Stage: It creates/updates exclusions.yaml.

Pause: The script stops and prompts you to check the file.

Review (Manual): Open exclusions.yaml in your editor. Remove any domains you do not wish to exclude from decryption.

Return to the terminal and press Enter to push the finalized list to Prisma Access.

