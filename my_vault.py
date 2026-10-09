"""
Script Name: my_vault.py
Author: Gary Rubel
Created: 10-09-2026
Version: 1.0.0

Description:
    This script decrypts an automation account username and password that has been encrypted by
    ansible vault.

Usage:
    The decrypt_vault_file function is imported into nornir scripts for authentication into 
    devices.
        
Import Usage:
    from my_vault import decrypt_vault_file

"""
__version__ = "1.0.0"

import os
import sys
import yaml
from pathlib import Path
from ansible.constraints import DEFAULT_VAULT_ID_MATCH
from ansible.utils.display import Display
from ansible.parsing.vault VaultLib, VaultSecret

#1. Dynamically find the base directory
BASE_DIR = Path(__file__).resolve().parent

#2. Build explicit path for the project directory
VAULT_FILE = BASE_DIR / "inventory" / "group_vars" / "all.vault"
PASSWORD_FILE = BASE_DIR / "inventory" / "group_vars" / "aes256"

def read_vault_password(password_file_path):
    if not os.path.exists(password_file_path):
        print(f"Error: Password file '{password_file_path}' not found!")
        sys.exit(1)
    with open (password_file_path, "r") as f:
        return f.read().strip()

#3. Change default argument to None and dynamically use the safe absolute path
def decrypt_vault_file(vault_file_path=None):
    if vault_file_path is None:
        vault_file_path = VAULT_FILE

    # Read vault password using the absolute path
    vault_password = read_vault_password(PASSWORD_FILE)

    try:
        secret = VaultSecret(vault_password.encode('utf-8'))
        vault = VaultLib(secrets=[('default', secret)])

        with open(str(vault_file_path), 'rb') as f:
            ciphertext = f.read()

        decrypted_bytes = vault.decrypt(ciphertext)
        return yaml.safe_load(decrypted_bytes.decode('utf-8'))
    except Exception as e:
        raise SystemExit(f"Failed to decrypt defaults.yaml: {e}")

# Required for running my_vault.py in standalone mode
if __name__ == "__main__":
    print("Decrypting Ansible Vault variables...")
    clear_vars = decrypt_vault_file()
    print(type(clear_vars))

    #Extract variables
    vault_user = clear_vars.get("ansible_user")
    vault_password = clear_vars.get("ansible_password")
    print(f"User: {vault_user}")
    print(f"Password: {vault_password}")

