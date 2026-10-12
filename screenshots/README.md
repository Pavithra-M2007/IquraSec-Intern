# Screenshots

This folder is for storing terminal screenshots of both tools in action.

## Required Screenshots

Capture the following screenshots to document your work for your internship review.
Use a tool like `scrot`, `gnome-screenshot`, or your desktop environment's screenshot key.

| Filename | Command to run |
|----------|---------------|
| `01_bash_help.png` | `bash bash_tool/security_checker.sh --help` |
| `02_bash_system.png` | `bash bash_tool/security_checker.sh --system` |
| `03_bash_disk.png` | `bash bash_tool/security_checker.sh --disk` |
| `04_bash_memory.png` | `bash bash_tool/security_checker.sh --memory` |
| `05_bash_firewall.png` | `bash bash_tool/security_checker.sh --firewall` |
| `06_bash_services.png` | `bash bash_tool/security_checker.sh --services` |
| `07_bash_permissions.png` | `bash bash_tool/security_checker.sh --permissions /tmp` |
| `08_python_help.png` | `python3 python_tool/file_integrity_checker.py --help` |
| `09_python_baseline.png` | `python3 python_tool/file_integrity_checker.py baseline --path test_data --output baseline.json` |
| `10_python_check_clean.png` | `python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json` |
| `11_python_check_modified.png` | Append a line to `test_data/sample.txt`, then run the check again |
| `12_unit_tests.png` | `python3 tests/test_file_integrity_checker.py -v` |

## Tips for Good Screenshots

- Make your terminal font large enough to read easily.
- Capture the full terminal window, including the command you ran.
- Use a dark terminal theme for better visibility.
- Name each file exactly as listed above so your mentor can identify them easily.

## No screenshots are pre-generated in this repository.

You must capture them yourself during a live demonstration.
