"""

Script Name: router-cmds.py
Author: Gary Rubel
Created: 10-12-2026
Version: 1.0.0

Description:
    This script use nornir to run "show commands" on juniper network devices

Standalone Usage: python router-cmds.py

Requirements:
        - my_inventory.py
        - my_vault.py

"""
__version__ = "1.0.0"

print(f"\nRun show commands!! {__version__}")

import os
import sys
import re
import types
import time
import yaml
import json
from datetime import timedelta
from getpass import getpass
import difflib
import glob
import pathlib
from pathlib import Path
from colorama import init, Fore

#Import nornir frameworks modules
from nornir import InitNornir
from nornir_netmiko import netmiko_send_command
from nornir_utils.plugins.functions import print_result
from nornir_utils.plugins.tasks.files import write_file
from nornir.core.task import Result
from nornir.core.filter import F

#Since we will import some custom python scripts, turn off duplicate distribution/namespace warning messages
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resource|ansible")
warnings.filterwarnings("ignore", message=".*distribution.*already load.*")

#Set directory structure for path to save files
work_dir = os.getcwd()
BACKUP_DIR = "backups"
REPORT_DIR = "reports"
cmd_dir = Path("./command_files")

#Create directories is case they don't exist
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)
if not os.path.exists(cmd_dir):
    os.makedirs(cmd_dir)

#Prompt for precheck or postcheck file, will be used in diff later
try:
    output_check = input("Enter '1' for prechecks, '2' for postchecks: ")
    output_dir = (os.path.join(work_dir, "reports/"))
except KeyboardInterrupt:
    print(f"User canceled! Exiting!!!")
    exit()

#Create a function to read all files is the ./command_files directory and list them to the user for selection
def load_cmd_file(target_dir):
    # Display available files
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"\nError: Directory '{target_dir}' does not exist!")
        return []

    available_files = list(target_dir.glob("*.txt"))
    if not available_files:
        print(f"\nNo '.txt' command files found in '{target_dir}'!")
        return []

    print("\n-----Avaiable command files-----")
    for file in available_files:
        print(f"\n{file.name}")
    print("-" * 32)

    while True:
        user_input = input("Enter the filename to load (or type 'exit'): ").strip()
        if user_input.lower() == 'exit':
            return []

        file_path = target_dir/user_input

        if file_path.exists() and file_path.is_file():
            break
        print(f"'{user_input}' not founds. Choose another file from the list \n")

    with open(file_path, "r", encoding="utf-8") as f:
        show_commands = [line.strip() for line in f if line.strip() and not line.startswith("#")]
      
    return show_commands

# Nornir function to run show commands
def run_juniper_show_cmds(task, commands):
    # Nornir task to run show commands from a file in ./command_files
    
    # Setup precheck and postcheck file options
    if output_check == "1":
        old_precheck_file = f"{REPORT_DIR}/{task.host}_precheck.txt"
        if os.path.exists(old_precheck_file):
            try:
                os.remove(old_precheck_file)
                print(f"\nDeleting old precheck file for {task.host}")
            except OSError as e:
                print(f"Erroring deleting '{old_precheck_file}': {e}")
        else:
            message = "No precheck files to delete"
    if output_check == "2":
        old_postcheck_file = f"{REPORT_DIR}/{task.host}_postcheck.txt"
        if os.path.exists(old_postcheck_file):
            try:
                os.remove(old_postcheck_file)
                print(f"\nDeleting old postcheck file for {task.host}")
            except OSError as e:
                print(f"Error deleting '{old_postcheck_file}': {e}")
        else:
            message = "No postcheck files to delete"

#Run nornir show command task
    for cmd in commands:
        output = task.run(
        task=netmiko_send_command,
        name=f"Running:{cmd}",
        command_string=cmd,
        delay_factor=10,
        read_timeout=300
        )

        if output_check == "1":
            output_file = f"{REPORT_DIR}/{task.host}_precheck.txt"
        if output_check == "2":
            output_file = f"{REPORT_DIR}/{task.host}_postcheck.txt"
        with open(output_file, 'a') as f:
            f.write(f"\n--->{cmd}\n")
            if output:
                f.write(output.result)
            os.chmod(output_file, 0o777)

    # Check for precheck and postcheck files so a diff can be run
    print(f"\n !!! Check if the precheck and postcheck files exist !!!")
    for my_host in {task.host}:
        try:
            with open(f"{REPORT_DIR}/{my_host}_precheck.txt", 'r') as f:
                pre_path = f.read()
                print(f"\n<<<<< Precheck outputs from {my_host} >>>>>")
                print(pre_path)
            with open(f"{REPORT_DIR}/{my_host}_postcheck.txt", 'r') as f:
                post_path = f.read()
                print(f"\n<<<<< Postcheck outputs from {my_host} >>>>")
                print(post_path)

            # Diff precheck and postcheck files
            lines1 = pre_path.splitlines(keepends=True)
            lines2 = post_path.splitlines(keepends=True)

            print(f"\n!!! Diff precheck and postcheck files !!!\n")
            diff = difflib.unified_diff(
                lines1,
                lines2,
                fromfile='Variable 1 Content',
                tofile='Variable 2 Content',
                n=3,
                lineterm=''
            )
            for line in diff:
                if line.startswith(" "):
                    print(Fore.WHITE + line[1:], end=" ")
                elif line.startswith('+'):
                    print(Fore.GREEN + line[1:], end=" ")
                elif line.startswith('-'):
                    print(Fore.RED + line[1:], end=" ")
                elif line.startswith(" "):
                    print(f" {line[1:]}", end=" ")
                elif line.startswith('@@'):
                    print("\n")
                    print(Fore.CYAN + line[1:], end=" ")
        except FileNotFoundError:
            print(f"\n!!! No postcheck file found !!!\n")
                

def main():
    start_time = time.perf_counter()
    
    #Run function to laod show command file
    show_commands = load_cmd_file(cmd_dir)
    print(show_commands)
    if not show_commands:
        return

    """
    Read in ansible inventory using a custome module --> my_inventory.py
    """
    from my_inventory import init_nornir_inventory, get_target_hosts

    #1. Initialize inventory 
    nr = init_nornir_inventory()

    #Set up looging to record the username running the script
    import logging
    import getpass
    logger = logging.getLogger("nornir")
    user_executer = getpass.getuser()
    #logger.info(f"---> router-cmds.py started by: {user_executer} <---")

    #2. Filter the inventory from user input
    filtered_nr = get_target_hosts(nr)

    #3. Print out filtered hosts and log user to nornir.log
    if filtered_nr:
        node_list = list(filtered_nr.inventory.hosts.keys())
        print(f"Targeting: {node_list}")
        logger.info(f" ---> router-cmds.py started by: {user_executer} against hosts {node_list}")

    #4. Inject the decrypted automation account username/password from my_vault.py and decrytes ansible-vault file
    from my_vault import decrypt_vault_file
    vault_data = decrypt_vault_file()
    username = vault_data.get("ansible_user")
    password = vault_data.get("ansible_password")
    #print(f"{username}:{password}")

    # Set username/password for each host
    for host_name, host_obj in nr.inventory.hosts.items():
        host_obj.username = username
        host_obj.password = password

    print("✅ Credentials injected successfully. Starting tasks...")

    print(f"\n Starting paralled show commands on {len(filtered_nr.inventory.hosts)} device(s) ...")
    results = filtered_nr.run(
        task=run_juniper_show_cmds,
        commands=show_commands
    )


    end_time = time.perf_counter()
    execution_time = end_time - start_time
    formatted_time = str(timedelta(seconds=execution_time))
    print(f"\nTotal run time for {len(filtered_nr.inventory.hosts)} device(s): ***{formatted_time} seconds***")
    
if __name__ == "__main__":
    main()
