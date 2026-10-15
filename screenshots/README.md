# Screenshots — Phase 1 Scripting & Automation

This folder contains screenshots documenting the execution and testing of the Bash and Python security tools developed for Phase 1 of the IqraSec Academy Cybersecurity Scripting & Automation Internship.

## Screenshot Documentation

### Bash Linux Security Checker

| Screenshot | Description |
|---|---|
| `01_bash_help.png` | Displays the available commands and usage instructions. |
| `02_bash_system.png` | Shows basic Linux system information. |
| `03_bash_disk.png` | Displays disk usage information. |
| `04_bash_memory.png` | Shows memory usage information. |
| `05_bash_firewall.png` | Displays firewall status information. |
| `06_bash_services.png` | Lists relevant system services and their status. |
| `07_bash_permissions.png` | Checks permissions for the specified directory. |

### Python File Integrity Checker

| Screenshot | Description |
|---|---|
| `08_python_help.png` | Displays the available commands and usage instructions. |
| `09_python_baseline.png` | Demonstrates creating a SHA-256 file integrity baseline. |
| `10_python_check_clean.png` | Shows the result when files match the saved baseline. |
| `11_python_check_modified.png` | Demonstrates detecting a modified file. |
| `12_unit_tests.png` | Shows the unit test execution results. |

## Notes

- The Bash tool performs read-only system checks.
- The Python tool creates a JSON baseline and compares file hashes to identify changes.
- Commands and outputs are documented to support verification and demonstration.
- Run the commands from the project root directory to reproduce the results.
