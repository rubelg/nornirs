"""
Script Name: my_inventory.py
Author: Gary Rubel
Created: 10-03-2026
Version: 1.0.0

Description:
    This script allows nornir scripts to use ansible inventories
    You can have multiple inventory files in either yaml or ini format

Standalone Usage: python my_inventory
        
Import Usage:
    from my_inventory import init_nornir_inventory, get_target_hosts

"""
__version__ = "1.0.0"

print(f"Read Ansible Inventree files: {__version__}")

import types
import sys
import os
import pathlib
from pathlib import Path
import glob
from itertools import chain
from nornir import InitNornir
from nornir.core.filter import F
from nornir_ansible.plugins.inventory import AnsibleInventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.inventory import ConnectionOptions

InventoryPluginRegister.register("AnsibleInventory", AnsibleInventory)
work_dir = os.getcwd()

# Create function to filter through loaded hosts and allow user to input target hosts
def get_target_hosts(nr, target_input=None):
    """
    Filter hosts if target_input is provided
    """
    user_input = target_input
    if not user_input:
        print("\nOptions: Enter and single host, a list of comma separated hosts, or a group name:")
        user_input = input("Enter target(s): ").strip()

    if not user_input:
        print("No input provided! Exiting!!!")
        return None

    if user_input in nr.inventory.groups:
        print(f"Filtering by group: '{user_input}'")
        return nr.filter(F(groups__contains=user_input))

    if "," in user_input:
        host_list = [h.strip() for h in user_input.split(",") if h.strip()]
    else:
        host_list = [user_input]

    print(host_list)

    filtered_nr = nr.filter(filter_func=lambda host: host.name in host_list)

    if not filtered_nr.inventory.hosts:
        print(f"Warning: No matching hosts found '{user_input}'")
    
    return filtered_nr

# Initialize ansible style inventree
def init_nornir_inventory():
    """
    Intialize inventory without prompting for input to make is safe for import into other scripts
    Allows for multiple inventory files on large networks
    """
    
    dir_path = Path("inventory")
    yaml_inv = dir_path.glob("*.yaml")
    ini_inv = dir_path.glob("*.ini")

    inventory_paths = [str(file) for file in chain(yaml_inv, ini_inv)]
    """
    For use with a single inventory file type
    inventory_paths = [str(file) for file in dir_path.glob("*.yaml")]
    """
    print("🚀 Initializing Nornirs...")
    nr = InitNornir(config_file="config.yaml")
    nr.inventory.hosts = {}
    nr.inventory.groups = {}
    
    for path in inventory_paths:
        temp_nr = InitNornir(
            inventory={
                "plugin": "AnsibleInventory",
                "options": {
                    "hostsfile": path
                }
            }
        )
        nr.inventory.hosts.update(temp_nr.inventory.hosts)
        nr.inventory.groups.update(temp_nr.inventory.groups)

    print(f"\nAvailable Hosts:\n {list(nr.inventory.hosts.keys())}\n")
    print(f"Available Groups:\n {list(nr.inventory.groups.keys())}")
    print("✅ Inventree injected successfully. Starting tasks...")
    
    return nr

def get_juniper_nodes():
    """
    Intializes inventory and dynamically extract hosts.
    Use this for retrieving inventory in external scripts
    """

    nr = init_nornir_inventory()
    # Replace this filter logic for the node type: "juniper", "aruba", etc
    # Can be platform type or group names
    juniper_hosts = [ host for host, data in nr.inventory.hosts.items() if data.platform == "juniper" or "juniper" in host]
    return juniper_hosts

# --- Standalone Execution to see what's in your inventree ---
# --- Executes only when running 'python my_inventory.py' directly

def main():
    nr = init_nornir_inventory()
    print(f"\nAvailable Hosts:\n {list(nr.inventory.hosts.keys())}\n")
    print(f"\nAvailable Groups:\n {list(nr.inventory.groups.keys())}\n")

    filtered_nr = get_target_hosts(nr)
    if filtered_nr:
        print(f"Target hosts: {list(filtered_nr.inventory.hosts.keys())}\n") 

    for name, host in filtered_nr.inventory.hosts.items():
        print(f"ip: {host.hostname} | port:{host.port} | platform:{host.platform}")

if __name__ == "__main__":
    main()
