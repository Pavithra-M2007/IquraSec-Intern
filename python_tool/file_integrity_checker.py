#!/usr/bin/env python3
"""
file_integrity_checker.py — File Integrity Checker
====================================================
Description:
    A command-line tool that detects unexpected changes to files by
    comparing their SHA-256 cryptographic hashes against a saved baseline.

    It can:
      • Calculate the SHA-256 hash of any file.
      • Scan a directory recursively to build a baseline.
      • Save that baseline to a JSON file.
      • Compare current files against a saved baseline.
      • Report modified, new, and missing files clearly.

    IMPORTANT LIMITATIONS:
      • A changed hash does NOT prove a file is malicious.
        It only means the file content has changed since the baseline was saved.
      • Always investigate changes in context — a system update or application
        upgrade can legitimately change many files.
      • This tool never overwrites a baseline silently; you must use the
        'baseline' command explicitly to create or update one.

Author  : IqraSec Internship — Phase 1
Version : 1.0.0
Python  : 3.8 or later (standard library only — no pip install needed)

Usage:
    python3 file_integrity_checker.py --help
    python3 file_integrity_checker.py baseline --path test_data --output baseline.json
    python3 file_integrity_checker.py check --path test_data --baseline baseline.json
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOOL_VERSION = "1.0.0"
BUFFER_SIZE  = 65536   # Read files in 64 KB chunks to handle large files
EXIT_OK      = 0       # No problems found
EXIT_CHANGES = 1       # Changes were detected (not necessarily malicious)
EXIT_ERROR   = 2       # A script error occurred (bad path, unreadable file, etc.)


# ---------------------------------------------------------------------------
# hash_file(filepath) → str | None
# ---------------------------------------------------------------------------
def hash_file(filepath: str) -> str | None:
    """
    Calculate the SHA-256 hash of a single file.

    SHA-256 is a cryptographic hash function. Given the same file content,
    it always produces the same 64-character hexadecimal string (the "hash").
    If even one byte of the file changes, the hash changes completely.

    Parameters
    ----------
    filepath : str
        The absolute or relative path to the file to hash.

    Returns
    -------
    str
        The lowercase hexadecimal SHA-256 digest string (64 characters).
    None
        If the file could not be read (does not exist, permission denied, etc.).
    """
    sha256 = hashlib.sha256()

    try:
        # Open the file in binary mode ('rb') so we read exact bytes
        with open(filepath, "rb") as fh:
            # Read in chunks to avoid loading huge files into memory at once
            while True:
                chunk = fh.read(BUFFER_SIZE)
                if not chunk:
                    break           # End of file
                sha256.update(chunk)
    except FileNotFoundError:
        print(f"  [ERROR] File not found: {filepath}", file=sys.stderr)
        return None
    except PermissionError:
        print(f"  [ERROR] Permission denied: {filepath}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"  [ERROR] Cannot read '{filepath}': {exc}", file=sys.stderr)
        return None

    return sha256.hexdigest()


# ---------------------------------------------------------------------------
# scan_directory(directory) → dict[str, str]
# ---------------------------------------------------------------------------
def scan_directory(directory: str) -> dict:
    """
    Recursively scan a directory and calculate SHA-256 hashes for all files.

    Symbolic links that point outside the given directory are skipped to
    prevent accidentally scanning unintended parts of the filesystem.

    Parameters
    ----------
    directory : str
        Path to the directory to scan.

    Returns
    -------
    dict
        A mapping of { relative_file_path: sha256_hash_or_"UNREADABLE" }.
        Paths are stored relative to 'directory' so the baseline is portable.
    """
    results = {}

    # Resolve the directory to an absolute real path (follow any symlinks once)
    try:
        base_path = os.path.realpath(directory)
    except OSError as exc:
        print(f"[ERROR] Cannot resolve path '{directory}': {exc}", file=sys.stderr)
        return results

    print(f"\n  Scanning directory: {base_path}")
    print(f"  Please wait...\n")

    # os.walk() visits every subdirectory; topdown=True means parent first
    for dirpath, dirnames, filenames in os.walk(base_path, topdown=True,
                                                followlinks=False):
        # Skip hidden directories (starting with '.') to avoid scanning
        # version-control internals like .git/
        # Modify the dirnames list IN PLACE to prevent os.walk from descending
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)

            # --- Guard against symlinks escaping the scan directory ---
            real_path = os.path.realpath(full_path)
            if not real_path.startswith(base_path):
                print(f"  [SKIP] Symlink points outside scan root: {full_path}",
                      file=sys.stderr)
                continue

            # Build a path relative to the scan root for portability
            relative_path = os.path.relpath(full_path, base_path)

            file_hash = hash_file(full_path)
            if file_hash is None:
                # We could not hash this file, but we record it so the user
                # knows it was seen — we mark it as UNREADABLE
                results[relative_path] = "UNREADABLE"
            else:
                results[relative_path] = file_hash

    print(f"  Scan complete. {len(results)} file(s) found.")
    return results


# ---------------------------------------------------------------------------
# save_baseline(hashes, output_path, scan_path) → bool
# ---------------------------------------------------------------------------
def save_baseline(hashes: dict, output_path: str, scan_path: str) -> bool:
    """
    Save a dictionary of file hashes to a JSON baseline file.

    The JSON file stores metadata (timestamp, scan path, tool version)
    alongside the hash data, making it easy to understand later.

    Parameters
    ----------
    hashes : dict
        Mapping of { relative_path: sha256_hash } from scan_directory().
    output_path : str
        Path where the JSON baseline file should be written.
    scan_path : str
        Original scan path (stored in metadata for reference).

    Returns
    -------
    bool
        True if the file was saved successfully, False otherwise.
    """
    # Structure the data with helpful metadata at the top level
    baseline_data = {
        "metadata": {
            "tool":       "file_integrity_checker.py",
            "version":    TOOL_VERSION,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "scan_path":  os.path.abspath(scan_path),
            "file_count": len(hashes),
        },
        "files": hashes,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as fh:
            # indent=2 makes the JSON human-readable
            json.dump(baseline_data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")          # End file with a newline (good practice)
    except PermissionError:
        print(f"[ERROR] Permission denied writing to: {output_path}",
              file=sys.stderr)
        return False
    except OSError as exc:
        print(f"[ERROR] Cannot write baseline to '{output_path}': {exc}",
              file=sys.stderr)
        return False

    return True


# ---------------------------------------------------------------------------
# load_baseline(baseline_path) → dict | None
# ---------------------------------------------------------------------------
def load_baseline(baseline_path: str) -> dict | None:
    """
    Load a previously saved JSON baseline file.

    Parameters
    ----------
    baseline_path : str
        Path to the JSON file created by save_baseline().

    Returns
    -------
    dict
        The parsed baseline data (the full JSON object).
    None
        If the file cannot be opened or contains invalid JSON.
    """
    if not os.path.exists(baseline_path):
        print(f"[ERROR] Baseline file not found: {baseline_path}", file=sys.stderr)
        return None

    if not os.path.isfile(baseline_path):
        print(f"[ERROR] Baseline path is not a file: {baseline_path}",
              file=sys.stderr)
        return None

    try:
        with open(baseline_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Baseline file contains invalid JSON: {exc}", file=sys.stderr)
        print(f"         File: {baseline_path}", file=sys.stderr)
        return None
    except PermissionError:
        print(f"[ERROR] Permission denied reading: {baseline_path}", file=sys.stderr)
        return None
    except OSError as exc:
        print(f"[ERROR] Cannot read baseline '{baseline_path}': {exc}",
              file=sys.stderr)
        return None

    # Basic structure validation — make sure the expected keys exist
    if "files" not in data:
        print(f"[ERROR] Baseline file is missing the 'files' key.", file=sys.stderr)
        print(f"         The file may be corrupted or created by a different tool.",
              file=sys.stderr)
        return None

    return data


# ---------------------------------------------------------------------------
# compare_files(baseline_hashes, current_hashes) → dict
# ---------------------------------------------------------------------------
def compare_files(baseline_hashes: dict, current_hashes: dict) -> dict:
    """
    Compare two sets of file hashes and classify every file.

    Categories:
      - unchanged : File exists in both baseline and current scan, same hash.
      - modified  : File exists in both, but the hash has changed.
      - new       : File exists now but was NOT in the baseline.
      - missing   : File was in the baseline but is NOT in the current scan.

    Parameters
    ----------
    baseline_hashes : dict
        The { path: hash } mapping from the saved baseline.
    current_hashes : dict
        The { path: hash } mapping from the current scan.

    Returns
    -------
    dict
        {
          "unchanged": [...],
          "modified":  [ {"path": ..., "baseline_hash": ..., "current_hash": ...}, ...],
          "new":       [...],
          "missing":   [...],
        }
    """
    results = {
        "unchanged": [],
        "modified":  [],
        "new":       [],
        "missing":   [],
    }

    # Check every file from the baseline against the current scan
    for path, baseline_hash in baseline_hashes.items():
        if path in current_hashes:
            current_hash = current_hashes[path]
            if current_hash == baseline_hash:
                results["unchanged"].append(path)
            else:
                # Hash mismatch — the file content has changed
                results["modified"].append({
                    "path":          path,
                    "baseline_hash": baseline_hash,
                    "current_hash":  current_hash,
                })
        else:
            # In baseline but not in current scan → deleted or moved
            results["missing"].append(path)

    # Check current scan for files NOT in the baseline
    for path in current_hashes:
        if path not in baseline_hashes:
            results["new"].append(path)

    return results


# ---------------------------------------------------------------------------
# print_comparison_report(comparison) → int
# ---------------------------------------------------------------------------
def print_comparison_report(comparison: dict) -> int:
    """
    Print a human-readable report of the comparison results.

    Parameters
    ----------
    comparison : dict
        The output of compare_files().

    Returns
    -------
    int
        EXIT_OK (0) if no changes found, EXIT_CHANGES (1) if changes detected.
    """
    unchanged = comparison["unchanged"]
    modified  = comparison["modified"]
    new_files = comparison["new"]
    missing   = comparison["missing"]

    print("\n" + "=" * 60)
    print("  FILE INTEGRITY REPORT")
    print("=" * 60)

    # --- Unchanged files ---
    print(f"\n  [PASS] Unchanged files: {len(unchanged)}")
    if unchanged:
        for path in sorted(unchanged):
            print(f"         ✓  {path}")

    # --- Modified files ---
    print(f"\n  [ALERT] Modified files: {len(modified)}")
    if modified:
        print("  NOTE: A changed hash means content changed — not that the")
        print("        file is malicious. Investigate changes in context.\n")
        for item in sorted(modified, key=lambda x: x["path"]):
            print(f"         ✗  {item['path']}")
            print(f"            Baseline : {item['baseline_hash']}")
            print(f"            Current  : {item['current_hash']}")
    else:
        print("         (none)")

    # --- New files ---
    print(f"\n  [INFO]  New files (not in baseline): {len(new_files)}")
    if new_files:
        for path in sorted(new_files):
            print(f"         +  {path}")
    else:
        print("         (none)")

    # --- Missing files ---
    print(f"\n  [INFO]  Missing files (in baseline, not found now): {len(missing)}")
    if missing:
        for path in sorted(missing):
            print(f"         -  {path}")
    else:
        print("         (none)")

    # --- Summary ---
    print("\n" + "-" * 60)
    total_changes = len(modified) + len(new_files) + len(missing)
    if total_changes == 0:
        print("  RESULT: No changes detected. All files match the baseline.")
        print("-" * 60 + "\n")
        return EXIT_OK
    else:
        print(f"  RESULT: {total_changes} change(s) detected.")
        print(f"          Modified: {len(modified)}  |  New: {len(new_files)}"
              f"  |  Missing: {len(missing)}")
        print("-" * 60 + "\n")
        return EXIT_CHANGES


# ---------------------------------------------------------------------------
# cmd_baseline(args) — handle the 'baseline' sub-command
# ---------------------------------------------------------------------------
def cmd_baseline(args: argparse.Namespace) -> int:
    """
    Build and save a new integrity baseline for a directory or file.

    This is the 'baseline' sub-command handler. It:
      1. Validates the source path.
      2. Scans the directory (or hashes a single file).
      3. Warns if an output file already exists (never overwrites silently).
      4. Saves the baseline JSON.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments (args.path, args.output).

    Returns
    -------
    int
        EXIT_OK on success, EXIT_ERROR on failure.
    """
    scan_path   = args.path
    output_path = args.output

    print(f"\n{'=' * 60}")
    print(f"  CREATE BASELINE")
    print(f"{'=' * 60}")
    print(f"  Source path : {scan_path}")
    print(f"  Output file : {output_path}")

    # --- Validate the source path ---
    if not os.path.exists(scan_path):
        print(f"\n[ERROR] Path does not exist: {scan_path}", file=sys.stderr)
        return EXIT_ERROR

    # --- Warn before overwriting an existing baseline ---
    if os.path.exists(output_path):
        print(f"\n  [WARNING] Baseline file already exists: {output_path}")
        print("  Running 'baseline' will OVERWRITE the existing baseline.")
        try:
            answer = input("  Type 'yes' to confirm overwrite, or anything else to cancel: ")
        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment (e.g. piped input) — do not overwrite
            print("\n[CANCELLED] Non-interactive mode. Use a new output filename.")
            return EXIT_ERROR
        if answer.strip().lower() != "yes":
            print("[CANCELLED] Baseline was NOT overwritten.")
            return EXIT_OK

    # --- Scan and hash ---
    if os.path.isfile(scan_path):
        # Single-file mode
        print(f"\n  Single file mode.")
        file_hash = hash_file(scan_path)
        if file_hash is None:
            return EXIT_ERROR
        filename = os.path.basename(scan_path)
        hashes = {filename: file_hash}
        print(f"  {filename}: {file_hash}")
    elif os.path.isdir(scan_path):
        hashes = scan_directory(scan_path)
    else:
        print(f"[ERROR] Path is neither a file nor a directory: {scan_path}",
              file=sys.stderr)
        return EXIT_ERROR

    if not hashes:
        print("\n  [WARNING] No files were found in the scan path.")
        print("  The baseline will be empty. This may not be what you intended.")

    # --- Save ---
    success = save_baseline(hashes, output_path, scan_path)
    if not success:
        return EXIT_ERROR

    print(f"\n  [OK] Baseline saved to: {output_path}")
    print(f"       Files recorded: {len(hashes)}")
    print(f"       Created at    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    return EXIT_OK


# ---------------------------------------------------------------------------
# cmd_check(args) — handle the 'check' sub-command
# ---------------------------------------------------------------------------
def cmd_check(args: argparse.Namespace) -> int:
    """
    Compare current files against a saved baseline and report changes.

    This is the 'check' sub-command handler.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments (args.path, args.baseline).

    Returns
    -------
    int
        EXIT_OK if no changes, EXIT_CHANGES if changes detected,
        EXIT_ERROR on failure.
    """
    scan_path     = args.path
    baseline_path = args.baseline

    print(f"\n{'=' * 60}")
    print(f"  INTEGRITY CHECK")
    print(f"{'=' * 60}")
    print(f"  Scan path    : {scan_path}")
    print(f"  Baseline file: {baseline_path}")

    # --- Validate scan path ---
    if not os.path.exists(scan_path):
        print(f"\n[ERROR] Scan path does not exist: {scan_path}", file=sys.stderr)
        return EXIT_ERROR

    # --- Load baseline ---
    baseline_data = load_baseline(baseline_path)
    if baseline_data is None:
        return EXIT_ERROR

    baseline_hashes = baseline_data["files"]
    meta = baseline_data.get("metadata", {})

    print(f"\n  Baseline created : {meta.get('created_at', 'unknown')}")
    print(f"  Baseline scanned : {meta.get('scan_path', 'unknown')}")
    print(f"  Files in baseline: {meta.get('file_count', len(baseline_hashes))}")

    # --- Scan current state ---
    if os.path.isfile(scan_path):
        file_hash = hash_file(scan_path)
        if file_hash is None:
            return EXIT_ERROR
        current_hashes = {os.path.basename(scan_path): file_hash}
    elif os.path.isdir(scan_path):
        current_hashes = scan_directory(scan_path)
    else:
        print(f"[ERROR] Scan path is neither a file nor a directory: {scan_path}",
              file=sys.stderr)
        return EXIT_ERROR

    # --- Compare ---
    comparison = compare_files(baseline_hashes, current_hashes)

    # --- Print report ---
    exit_code = print_comparison_report(comparison)
    return exit_code


# ---------------------------------------------------------------------------
# cmd_hash(args) — handle the 'hash' sub-command (single-file hash display)
# ---------------------------------------------------------------------------
def cmd_hash(args: argparse.Namespace) -> int:
    """
    Display the SHA-256 hash of a single file without saving anything.

    Useful for quickly checking what a file's hash is, or verifying
    a downloaded file against a known hash.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments (args.file).

    Returns
    -------
    int
        EXIT_OK on success, EXIT_ERROR on failure.
    """
    target = args.file

    if not os.path.exists(target):
        print(f"[ERROR] File not found: {target}", file=sys.stderr)
        return EXIT_ERROR

    if not os.path.isfile(target):
        print(f"[ERROR] Not a file: {target}", file=sys.stderr)
        return EXIT_ERROR

    file_hash = hash_file(target)
    if file_hash is None:
        return EXIT_ERROR

    print(f"\nSHA-256: {file_hash}  {target}\n")
    return EXIT_OK


# ---------------------------------------------------------------------------
# build_argument_parser() → argparse.ArgumentParser
# ---------------------------------------------------------------------------
def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser for the tool.

    The tool uses sub-commands (like git):
      baseline  — create a new baseline
      check     — compare current files against a baseline
      hash      — display the SHA-256 hash of a file

    Returns
    -------
    argparse.ArgumentParser
        Fully configured parser ready to call parse_args() on.
    """
    parser = argparse.ArgumentParser(
        prog="file_integrity_checker.py",
        description=(
            "File Integrity Checker — detect changes to files using SHA-256 hashes.\n"
            "Use 'baseline' to create a snapshot and 'check' to compare later."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "EXAMPLES:\n"
            "  python3 file_integrity_checker.py baseline --path test_data "
            "--output baseline.json\n"
            "  python3 file_integrity_checker.py check --path test_data "
            "--baseline baseline.json\n"
            "  python3 file_integrity_checker.py hash --file myfile.txt\n\n"
            "DISCLAIMER:\n"
            "  A changed hash means a file's content changed — not that it is malicious.\n"
            "  Always investigate changes in the appropriate context.\n"
        ),
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"file_integrity_checker.py v{TOOL_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True   # A sub-command is mandatory

    # --- 'baseline' sub-command ---
    baseline_parser = subparsers.add_parser(
        "baseline",
        help="Scan a path and save a new integrity baseline.",
        description="Scan a directory or file and save SHA-256 hashes to a JSON baseline file.",
    )
    baseline_parser.add_argument(
        "--path", "-p",
        required=True,
        metavar="PATH",
        help="Directory or file to scan.",
    )
    baseline_parser.add_argument(
        "--output", "-o",
        required=True,
        metavar="OUTPUT_FILE",
        help="Path to save the baseline JSON file (e.g. baseline.json).",
    )
    baseline_parser.set_defaults(func=cmd_baseline)

    # --- 'check' sub-command ---
    check_parser = subparsers.add_parser(
        "check",
        help="Compare current files against a saved baseline.",
        description=(
            "Scan a directory or file and compare the results against a baseline.\n"
            "Reports modified, new, and missing files."
        ),
    )
    check_parser.add_argument(
        "--path", "-p",
        required=True,
        metavar="PATH",
        help="Directory or file to scan.",
    )
    check_parser.add_argument(
        "--baseline", "-b",
        required=True,
        metavar="BASELINE_FILE",
        help="Path to the baseline JSON file to compare against.",
    )
    check_parser.set_defaults(func=cmd_check)

    # --- 'hash' sub-command ---
    hash_parser = subparsers.add_parser(
        "hash",
        help="Display the SHA-256 hash of a single file.",
        description="Calculate and display the SHA-256 hash of a file without saving anything.",
    )
    hash_parser.add_argument(
        "--file", "-f",
        required=True,
        metavar="FILE",
        help="Path to the file to hash.",
    )
    hash_parser.set_defaults(func=cmd_hash)

    return parser


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Parse arguments and dispatch to the appropriate sub-command handler.
    """
    parser = build_argument_parser()
    args   = parser.parse_args()

    # Each sub-command sets args.func to its handler function
    exit_code = args.func(args)
    sys.exit(exit_code)


# Run main only when this script is executed directly,
# not when it is imported as a module (important for unit testing).
if __name__ == "__main__":
    main()
