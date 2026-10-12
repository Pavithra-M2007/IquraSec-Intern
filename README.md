# Phase 1 — Scripting & Automation Internship

## Project Title: Linux Security Tools — Bash & Python

---

## 1. Project Overview

This repository contains two fully functional, read-only command-line security tools built as part of **Phase 1** of the IqraSec Cybersecurity Scripting & Automation Internship.

| Tool | Language | Purpose |
|------|----------|---------
| `security_checker.sh` | Bash | Inspect a Linux system for common security issues |
| `file_integrity_checker.py` | Python 3 | Detect unexpected changes to files using SHA-256 hashes |

Both tools are **read-only** — they never change any system settings or files.

---

## 2. Objectives

- Learn how to write practical security scripts in Bash and Python.
- Understand core Linux security concepts: file permissions, firewall status, disk usage, and running services.
- Learn what cryptographic hashing is and how it detects file changes.
- Practice writing clean, commented, and beginner-friendly code.
- Gain experience with command-line argument parsing, error handling, and unit testing.

---

## 3. Features

### Bash Security Checker (`bash_tool/security_checker.sh`)

| Feature | Description |
|---------|-------------|
| `--system` | Shows current user, hostname, OS version, kernel, and uptime |
| `--disk` | Reports disk usage for real filesystems; warns if any is over 75% full |
| `--memory` | Reports RAM and swap usage with percentage thresholds |
| `--firewall` | Checks status of iptables, UFW, or firewalld (read-only) |
| `--services` | Lists all currently running systemd services |
| `--permissions PATH` | Finds world-writable files and SUID/SGID files in a directory |
| `--all` | Runs all of the above checks in sequence |
| `--help` | Displays usage instructions |
| `--version` | Displays tool version |

- Reports results as **PASS**, **WARNING**, **INFO**, or **ERROR**
- Never modifies any system settings
- Gracefully handles missing commands and permission errors
- Provides practical recommendations for any warnings found
- Virtual filesystems (tmpfs, devtmpfs, etc.) are excluded from disk checks

### Python File Integrity Checker (`python_tool/file_integrity_checker.py`)

| Feature | Description |
|---------|-------------|
| `baseline` | Scans a directory recursively and saves SHA-256 hashes to JSON |
| `check` | Compares current files against a saved baseline |
| `hash` | Displays the SHA-256 hash of a single file |
| `--help` | Displays full usage instructions (available at every level) |
| `--version` | Displays tool version |

- Detects **modified**, **new**, and **missing** files
- Stores baselines in human-readable JSON with metadata
- Never overwrites a baseline silently — prompts for confirmation
- Does not follow symlinks outside the scan directory
- Clear output with explicit PASS/ALERT/INFO labels
- Uses Python standard library only — no `pip install` required

---

## 4. Tools and Technologies

| Component | Technology |
|-----------|-----------|
| Shell scripting | Bash 4+ |
| Python scripting | Python 3.8+ |
| Hashing algorithm | SHA-256 (via Python `hashlib`) |
| Baseline storage | JSON (via Python `json`) |
| Argument parsing | Python `argparse` |
| Unit testing | Python `unittest` |
| Linux utilities | `find`, `df`, `free`, `systemctl`, `iptables`, `stat`, `uname` |

---

## 5. Requirements

- **Operating System**: Any modern Linux distribution (tested on Kali Linux 6.18)
- **Bash**: Version 4.0 or later (`bash --version`)
- **Python**: Version 3.8 or later (`python3 --version`)
- **No external packages required** — both tools use only what is built into the OS

---

## 6. Installation and Setup

```bash
# 1. Clone or copy the project folder
cd /home/pavi/IqraSec

# 2. Enter the project directory
cd phase1-scripting-automation

# 3. Make the Bash script executable (optional — you can also run with 'bash ...')
chmod +x bash_tool/security_checker.sh

# 4. Verify Python is available
python3 --version
```

No virtual environment or `pip install` is needed.

---

## 7. Folder Structure

```
phase1-scripting-automation/
├── README.md                          ← This file
├── .gitignore                         ← Files/folders excluded from git
├── bash_tool/
│   └── security_checker.sh           ← Bash security checker script
├── python_tool/
│   └── file_integrity_checker.py     ← Python file integrity checker
├── test_data/
│   ├── README.md                      ← Notes about the test data
│   ├── sample.txt                     ← Sample file for testing
│   ├── config.conf                    ← Sample config file for testing
│   └── subdir/
│       └── nested.txt                 ← File in subdirectory (tests recursion)
├── tests/
│   └── test_file_integrity_checker.py ← Automated unit tests (27 tests)
└── screenshots/
    └── README.md                      ← Screenshot capture instructions
```

> **Note:** The `reports/` folder is not part of this submission. There is no need to create it unless you have an actual report file to commit.

---

## 8. Running the Bash Security Checker

Always run from inside the `phase1-scripting-automation/` directory.

### Show help
```bash
bash bash_tool/security_checker.sh --help
```

### Show version
```bash
bash bash_tool/security_checker.sh --version
```

### Check system information
```bash
bash bash_tool/security_checker.sh --system
```

### Check disk usage
```bash
bash bash_tool/security_checker.sh --disk
```

### Check memory and swap
```bash
bash bash_tool/security_checker.sh --memory
```

### Check firewall status
```bash
bash bash_tool/security_checker.sh --firewall
# For full iptables details, run with sudo:
sudo bash bash_tool/security_checker.sh --firewall
```

### List running services
```bash
bash bash_tool/security_checker.sh --services
```

### Check a directory for world-writable files
```bash
bash bash_tool/security_checker.sh --permissions /tmp
bash bash_tool/security_checker.sh --permissions /home
bash bash_tool/security_checker.sh --permissions test_data
```

### Run all checks at once
```bash
bash bash_tool/security_checker.sh --all
```

---

## 9. Running the Python File Integrity Checker

Always run from inside the `phase1-scripting-automation/` directory.

### Show help
```bash
python3 python_tool/file_integrity_checker.py --help
python3 python_tool/file_integrity_checker.py baseline --help
python3 python_tool/file_integrity_checker.py check --help
```

### Step 1 — Create a baseline (snapshot of file hashes)
```bash
python3 python_tool/file_integrity_checker.py baseline \
    --path test_data \
    --output baseline.json
```

### Step 2 — Check files against the baseline (no changes yet)
```bash
python3 python_tool/file_integrity_checker.py check \
    --path test_data \
    --baseline baseline.json
```

### Step 3 — Simulate a file modification and re-check
```bash
echo "This line was added after the baseline!" >> test_data/sample.txt

python3 python_tool/file_integrity_checker.py check \
    --path test_data \
    --baseline baseline.json
```

### Step 4 — Hash a single file
```bash
python3 python_tool/file_integrity_checker.py hash \
    --file test_data/sample.txt
```

### Restore test data after testing
```bash
# Restore sample.txt to its original content:
cat > test_data/sample.txt << 'EOF'
This is a sample file for the File Integrity Checker.
It contains some text that will be hashed.
If you modify this content, the checker will detect a change.
EOF
```

---

## 10. Sample Output

> **Note**: The output below is representative of actual runs on Kali Linux 6.18.
> Exact values (percentages, uptime, timestamps) will vary on your system.

### Bash — `--system`
```
========================================
  System Information
========================================
  [INFO]    Current user   : pavi
  [PASS]    Running as a non-root user (pavi).
  [INFO]    Hostname       : kali
  [INFO]    OS             : Kali GNU/Linux Rolling
  [INFO]    Kernel version : 6.18.12+kali-amd64
  [INFO]    Uptime         : up 21 minutes
```

### Bash — `--disk`
```
========================================
  Disk Usage
========================================
  [INFO]    Disk usage for all real mounted filesystems:

    /dev/sda1        39G   21G   16G  58% /

  [PASS]    Filesystem '/' usage is 58% — within safe limits.
```
> Virtual filesystems (tmpfs, udev, etc.) are intentionally excluded from both the display and the PASS/WARNING checks.

### Bash — `--memory`
```
========================================
  Memory & Swap Usage
========================================
  [INFO]    Current memory status:

                 total        used        free      shared  buff/cache   available
  Mem:           3.8Gi       1.0Gi       1.8Gi        16Mi       1.3Gi       2.8Gi
  Swap:          2.2Gi          0B       2.2Gi

  [PASS]    RAM usage is 26% (1053MB / 3919MB) — normal.
  [PASS]    Swap usage is 0% — acceptable.
```

### Bash — `--firewall` (as regular user)
```
========================================
  Firewall Status
========================================
  [INFO]    iptables is available on this system.
  [ERROR]   Could not read iptables rules (likely need root privileges).
  [INFO]    Try: sudo iptables -L -n -v
```
> The `[ERROR]` here is expected and honest — iptables requires root to list rules. This is not a script bug.

### Python — create baseline
```
============================================================
  CREATE BASELINE
============================================================
  Source path : test_data
  Output file : baseline.json

  Scanning directory: .../phase1-scripting-automation/test_data
  Please wait...

  Scan complete. 4 file(s) found.

  [OK] Baseline saved to: baseline.json
       Files recorded: 4
       Created at    : 2026-10-12 09:48:00
```

### Python — check after modifying a file
```
============================================================
  FILE INTEGRITY REPORT
============================================================

  [PASS] Unchanged files: 3
         ✓  config.conf
         ✓  README.md
         ✓  subdir/nested.txt

  [ALERT] Modified files: 1
  NOTE: A changed hash means content changed — not that the
        file is malicious. Investigate changes in context.

         ✗  sample.txt
            Baseline : 8ac7ca945b531049...
            Current  : ec608ad8fb6e3afc...

  RESULT: 1 change(s) detected.
          Modified: 1  |  New: 0  |  Missing: 0
```

---

## 11. Running the Automated Tests

```bash
# Run all 27 unit tests with verbose output
python3 tests/test_file_integrity_checker.py -v
```

### Actual Test Results (verified 2026-10-12, Kali Linux 6.18, Python 3.13)

```
test_all_categories_together (TestCompareFiles) ... ok
test_empty_baseline_and_current (TestCompareFiles) ... ok
test_missing_file_detected (TestCompareFiles) ... ok
test_modified_file (TestCompareFiles) ... ok
test_new_file_detected (TestCompareFiles) ... ok
test_unchanged_file (TestCompareFiles) ... ok
test_detects_deleted_file (TestEndToEnd) ... ok
test_detects_modified_file (TestEndToEnd) ... ok
test_detects_new_file (TestEndToEnd) ... ok
test_no_changes_after_baseline (TestEndToEnd) ... ok
test_different_content_different_hash (TestHashFile) ... ok
test_empty_file_returns_hash (TestHashFile) ... ok
test_hash_known_value (TestHashFile) ... ok
test_hash_returns_64_char_hex_string (TestHashFile) ... ok
test_nonexistent_file_returns_none (TestHashFile) ... ok
test_same_content_same_hash (TestHashFile) ... ok
test_load_invalid_json_returns_none (TestSaveAndLoadBaseline) ... ok
test_load_missing_files_key_returns_none (TestSaveAndLoadBaseline) ... ok
test_load_nonexistent_returns_none (TestSaveAndLoadBaseline) ... ok
test_save_and_load_round_trip (TestSaveAndLoadBaseline) ... ok
test_save_creates_file (TestSaveAndLoadBaseline) ... ok
test_saved_baseline_has_metadata (TestSaveAndLoadBaseline) ... ok
test_scan_empty_directory (TestScanDirectory) ... ok
test_scan_finds_nested_files (TestScanDirectory) ... ok
test_scan_finds_top_level_files (TestScanDirectory) ... ok
test_scan_returns_hashes (TestScanDirectory) ... ok
test_scan_uses_relative_paths (TestScanDirectory) ... ok

----------------------------------------------------------------------
Ran 27 tests in 0.018s

OK
```

> **Note:** In Python 3.13 verbose mode, test names appear with their class in parentheses, e.g.
> `test_modified_file (__main__.TestCompareFiles.test_modified_file)`. The table above shows the
> simplified form for readability.

**Result: 27/27 tests passed.**

### Bash syntax validation
```bash
bash -n bash_tool/security_checker.sh
# Expected: no output (no syntax errors found)
```

---

## 12. Limitations and Safety Notes

### Bash Security Checker
- **Read-only**: The script never modifies system settings, firewall rules, or service configurations.
- **Firewall check**: The `iptables` check requires root to see rules. As a regular user it will show `[ERROR]` and suggest `sudo`. This is expected and honest — the script does not claim success when a check cannot be completed.
- **Permissions check on /tmp**: `/tmp` is intentionally world-writable on Linux. The `[WARNING]` for `/tmp` itself is normal.
- **Virtual filesystems**: `tmpfs`, `devtmpfs`, `udev`, and similar virtual filesystems are excluded from disk usage checks by design — they are not real storage devices.
- **Exit codes**: The script exits with code 1 when an invalid path or unknown option is provided.
- **Not a replacement for dedicated tools**: This is a learning exercise. For production environments, use dedicated security scanners (Lynis, OpenSCAP, etc.).

### Python File Integrity Checker
- **A changed hash does NOT mean a file is malicious.** It means the file content has changed. System updates legitimately change many files.
- **Baseline is a snapshot in time.** Always re-create the baseline after legitimate changes (updates, configuration changes).
- **Does not detect all threats**: This tool detects content changes. It cannot detect rootkits that intercept file reads.
- **Symbolic links**: The tool skips symlinks that point outside the scan directory to prevent accidentally scanning unintended paths.
- **Non-interactive mode**: If stdin is not a terminal (e.g. piped), the overwrite confirmation is declined automatically to avoid destructive behaviour.
- **Do not scan systems you do not own.**

---

## 13. Capturing Screenshots

Screenshot the following commands and save them in the `screenshots/` folder.
Use your terminal's built-in screenshot feature, `scrot`, or `gnome-screenshot`.

| Filename | Command to run |
|----------|----------------|
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
| `11_python_check_modified.png` | Append a line to `test_data/sample.txt`, then run the check command again |
| `12_unit_tests.png` | `python3 tests/test_file_integrity_checker.py -v` |

> Screenshots must be captured from real terminal sessions on your own machine.
> Do not include fake or placeholder images.

---

## 14. Troubleshooting

| Problem | Solution |
|---------|---------|
| `bash: security_checker.sh: Permission denied` | Run with `bash bash_tool/security_checker.sh ...` or first run `chmod +x bash_tool/security_checker.sh` |
| `python3: command not found` | Install Python 3: `sudo apt install python3` |
| `[ERROR] Could not read iptables rules` | Expected without root. Run `sudo bash bash_tool/security_checker.sh --firewall` |
| `[ERROR] Baseline file not found` | Run the `baseline` command first before `check` |
| `[ERROR] Baseline file contains invalid JSON` | The baseline file is corrupted. Re-create it with the `baseline` command |
| Python version error | Upgrade Python: `sudo apt update && sudo apt install python3` |
| `bash -n` reports a syntax error | Check the line number shown; look for unclosed quotes or brackets |
| Script exits with code 1 for `--permissions` | Check that the given path exists and is a directory |

---

## 15. Conclusion and Learning Outcomes

By completing this phase, you have:

1. **Written a real Bash security tool** that reads system state, parses command output, handles errors gracefully, and provides actionable feedback.
2. **Written a Python cryptography-based tool** that uses SHA-256 hashing to detect file changes.
3. **Learned about file permissions** — world-writable files and SUID bits can be security risks.
4. **Understood baselines** — creating a known-good snapshot and comparing against it is a fundamental security practice.
5. **Practised error handling** — the tools gracefully handle missing files, permission errors, bad input, and corrupted data.
6. **Written 27 automated unit tests** — testing proves the code works correctly without manual re-checking every time.
7. **Followed secure coding principles**: read-only operations, no hardcoded credentials, no scanning of systems you don't own, and honest result reporting (no false PASSes).

---

*IqraSec Cybersecurity Internship — Phase 1 | Kali Linux 6.18 | Python 3.13 | Bash 5.3*
