# Test Data

This folder contains sample files used to demonstrate and test the File Integrity Checker.

## Files

| File | Purpose |
|------|---------|
| `sample.txt` | A simple text file — modify this to trigger a MODIFIED detection |
| `config.conf` | A simulated configuration file — delete this to trigger a MISSING detection |
| `subdir/nested.txt` | A file in a subdirectory — tests that the scanner works recursively |

## How to Use for Testing

```bash
# 1. Create a baseline (from the project root)
python3 python_tool/file_integrity_checker.py baseline --path test_data --output baseline.json

# 2. Verify no changes
python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json

# 3. Simulate a modification — append a line to sample.txt
echo "Unauthorised change!" >> test_data/sample.txt

# 4. Re-check — should detect 1 modified file
python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json

# 5. Simulate adding a new file
echo "I was added after the baseline" > test_data/new_file.txt
python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json

# 6. Simulate deleting a file
rm test_data/config.conf
python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json
```

## IMPORTANT

Do NOT store real passwords, API keys, private configuration files, or
personal data in this folder. This directory is for demonstration purposes only.
