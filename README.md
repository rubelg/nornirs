# nornir

This repo is a python nornir structure using ansible inventory files and ansible vault

Nornir normally operates on a set of required files show below:

```text
├── config.yaml          # Main Nornir configuration
├── inventory/           # Folder containing your target devices
│   ├── hosts.yaml       # Specific device details
│   ├── groups.yaml      # Shared device configurations
│   └── defaults.yaml    # Global credentials/settings
└── run_script.py        # Your Python execution script
```

Using an Ansible style inventree allows you to configure the hosts and groups in one file.
When using an ansible style inventory and ansible-vault, the file structure is this:

```text
├── config.yaml
├── inventory
│   ├── group_vars
│   │   ├── aes256
│   │   └── all.vault
│   ├── routers.yaml
│   ├── srx.ini
│   └── srx.old
├── my_inventory.py
├── my_inventree
├── my_vault.py
├── nornir.log
└── README.md
```
