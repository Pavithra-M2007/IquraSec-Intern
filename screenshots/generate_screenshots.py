#!/usr/bin/env python3
"""
generate_screenshots.py
=======================
Generates 12 terminal-style PNG screenshots for the Phase 1 README.

Each screenshot simulates a dark terminal window showing the real output
of the corresponding command. All output text comes from actual command runs.

Usage:
    python3 screenshots/generate_screenshots.py
"""

import os
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCREENSHOTS_DIR = Path(__file__).parent
REPO_ROOT       = SCREENSHOTS_DIR.parent

FONT_PATH   = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE   = 14
LINE_HEIGHT = 18
PADDING_X   = 18
PADDING_Y   = 40   # Space for title bar
TITLE_H     = 26

# Colours matching a dark terminal
BG_COLOR       = (22, 22, 29)       # Near-black background
TITLE_BG       = (40, 40, 50)       # Slightly lighter title bar
TEXT_COLOR     = (220, 220, 220)    # Default white-ish text
GREEN_COLOR    = (80, 200, 120)     # PASS / [OK]
YELLOW_COLOR   = (240, 200, 60)     # WARNING / prompt
RED_COLOR      = (230, 90, 80)      # ERROR / ALERT
CYAN_COLOR     = (80, 200, 220)     # INFO / header / bash prompt
GRAY_COLOR     = (140, 140, 160)    # dim text


def load_font(size=FONT_SIZE):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def colour_for_line(line: str):
    """Pick a colour based on keywords in the output line."""
    stripped = line.strip()
    if stripped.startswith("[PASS]") or stripped.startswith("✓") or \
       stripped.startswith("[OK]") or "PASS" in stripped and ":" in stripped:
        return GREEN_COLOR
    if stripped.startswith("[WARNING]") or stripped.startswith("→ Recommendation"):
        return YELLOW_COLOR
    if stripped.startswith("[ERROR]") or stripped.startswith("[ALERT]") or \
       stripped.startswith("✗"):
        return RED_COLOR
    if stripped.startswith("[INFO]") or stripped.startswith("===") or \
       stripped.startswith("---") or stripped.startswith("DESCRIPTION") or \
       stripped.startswith("USAGE") or stripped.startswith("OPTIONS") or \
       stripped.startswith("EXAMPLES") or stripped.startswith("NOTES") or \
       stripped.startswith("RESULT:") or stripped.startswith("Running ") or \
       stripped.startswith("Scan") or stripped.startswith("Please") or \
       stripped.startswith("FILE INTEGRITY") or stripped.startswith("CREATE BASELINE") or \
       stripped.startswith("INTEGRITY CHECK") or "======" in stripped or \
       "------" in stripped:
        return CYAN_COLOR
    if stripped.startswith("$") or stripped.startswith("pavi@kali"):
        return CYAN_COLOR
    if stripped.startswith("#") or stripped.startswith("Baseline") or \
       stripped.startswith("Current") or stripped.startswith("NOTE:"):
        return GRAY_COLOR
    return TEXT_COLOR


def render_screenshot(title: str, command_line: str, output_text: str,
                      filename: str, width: int = 860):
    """Render a dark-terminal PNG with command + output."""
    font = load_font(FONT_SIZE)
    title_font = load_font(FONT_SIZE - 1)

    # Wrap and split lines
    raw_lines = []
    raw_lines.append(f"pavi@kali:~/IqraSec/phase1-scripting-automation$ {command_line}")
    raw_lines.append("")
    for line in output_text.split("\n"):
        # Wrap very long lines
        if len(line) > 110:
            for wrapped in textwrap.wrap(line, width=110):
                raw_lines.append(wrapped)
        else:
            raw_lines.append(line)

    # Trim trailing blank lines but keep one blank at end
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    raw_lines.append("")

    total_lines = len(raw_lines)
    img_height  = PADDING_Y + (total_lines * LINE_HEIGHT) + PADDING_Y // 2

    img  = Image.new("RGB", (width, img_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, width, TITLE_H], fill=TITLE_BG)
    # Traffic-light dots
    for x_dot, dot_color in [(14, (255, 95, 86)), (34, (255, 189, 46)), (54, (39, 201, 63))]:
        draw.ellipse([x_dot - 6, TITLE_H // 2 - 6, x_dot + 6, TITLE_H // 2 + 6], fill=dot_color)
    # Title text
    draw.text((width // 2, TITLE_H // 2), title,
              font=title_font, fill=(180, 180, 190), anchor="mm")

    # Output lines
    y = PADDING_Y
    for line in raw_lines:
        color = colour_for_line(line)
        # Prompt line gets special cyan colouring for the prompt part
        if line.startswith("pavi@kali"):
            # Split at $
            idx = line.find("$")
            if idx >= 0:
                draw.text((PADDING_X, y), line[:idx + 1], font=font, fill=CYAN_COLOR)
                cmd_x = PADDING_X + (idx + 1) * (FONT_SIZE * 0.60)
                draw.text((int(cmd_x), y), line[idx + 1:], font=font, fill=(255, 255, 180))
            else:
                draw.text((PADDING_X, y), line, font=font, fill=CYAN_COLOR)
        else:
            draw.text((PADDING_X, y), line, font=font, fill=color)
        y += LINE_HEIGHT

    out_path = SCREENSHOTS_DIR / filename
    img.save(out_path, "PNG")
    print(f"  Saved: {out_path.name}  ({width}×{img_height}px)")
    return out_path


def run(cmd: str, cwd=None) -> str:
    """Run a shell command and return its combined stdout+stderr."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=str(cwd or REPO_ROOT)
    )
    out = (result.stdout + result.stderr).strip()
    return out


def main():
    print("\nGenerating Phase 1 screenshots...\n")

    cwd = REPO_ROOT

    # ------------------------------------------------------------------
    # 01  Bash help
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --help", cwd)
    render_screenshot(
        title="01 — Bash Help",
        command_line="bash bash_tool/security_checker.sh --help",
        output_text=out,
        filename="01_bash_help.png",
    )

    # ------------------------------------------------------------------
    # 02  Bash system information
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --system", cwd)
    render_screenshot(
        title="02 — Bash System Information",
        command_line="bash bash_tool/security_checker.sh --system",
        output_text=out,
        filename="02_bash_system.png",
    )

    # ------------------------------------------------------------------
    # 03  Bash disk usage
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --disk", cwd)
    render_screenshot(
        title="03 — Bash Disk Usage",
        command_line="bash bash_tool/security_checker.sh --disk",
        output_text=out,
        filename="03_bash_disk.png",
    )

    # ------------------------------------------------------------------
    # 04  Bash memory usage
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --memory", cwd)
    render_screenshot(
        title="04 — Bash Memory Usage",
        command_line="bash bash_tool/security_checker.sh --memory",
        output_text=out,
        filename="04_bash_memory.png",
    )

    # ------------------------------------------------------------------
    # 05  Bash firewall status
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --firewall", cwd)
    render_screenshot(
        title="05 — Bash Firewall Status",
        command_line="bash bash_tool/security_checker.sh --firewall",
        output_text=out,
        filename="05_bash_firewall.png",
    )

    # ------------------------------------------------------------------
    # 06  Bash running services
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --services", cwd)
    render_screenshot(
        title="06 — Bash Running Services",
        command_line="bash bash_tool/security_checker.sh --services",
        output_text=out,
        filename="06_bash_services.png",
        width=980,
    )

    # ------------------------------------------------------------------
    # 07  Bash permission scan on test_data
    # ------------------------------------------------------------------
    out = run("bash bash_tool/security_checker.sh --permissions test_data", cwd)
    render_screenshot(
        title="07 — Bash Permission Scan",
        command_line="bash bash_tool/security_checker.sh --permissions test_data",
        output_text=out,
        filename="07_bash_permissions.png",
    )

    # ------------------------------------------------------------------
    # 08  Python help
    # ------------------------------------------------------------------
    out = run("python3 python_tool/file_integrity_checker.py --help", cwd)
    render_screenshot(
        title="08 — Python Help",
        command_line="python3 python_tool/file_integrity_checker.py --help",
        output_text=out,
        filename="08_python_help.png",
    )

    # ------------------------------------------------------------------
    # 09  Python baseline creation
    # ------------------------------------------------------------------
    # Use a temp baseline so we don't pollute the repo
    import tempfile, os
    tmp_baseline = os.path.join(tempfile.gettempdir(), "phase1_ss_baseline.json")
    # Remove if leftover from a previous run
    if os.path.exists(tmp_baseline):
        os.remove(tmp_baseline)

    out = run(
        f"python3 python_tool/file_integrity_checker.py baseline "
        f"--path test_data --output {tmp_baseline}",
        cwd
    )
    render_screenshot(
        title="09 — Python Baseline Creation",
        command_line="python3 python_tool/file_integrity_checker.py baseline --path test_data --output baseline.json",
        output_text=out,
        filename="09_python_baseline.png",
    )

    # ------------------------------------------------------------------
    # 10  Python check (unchanged)
    # ------------------------------------------------------------------
    out = run(
        f"python3 python_tool/file_integrity_checker.py check "
        f"--path test_data --baseline {tmp_baseline}",
        cwd
    )
    render_screenshot(
        title="10 — Python Check (No Changes)",
        command_line="python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json",
        output_text=out,
        filename="10_python_check_clean.png",
    )

    # ------------------------------------------------------------------
    # 11  Python check after modifying a file (safe restore)
    # ------------------------------------------------------------------
    sample_path = cwd / "test_data" / "sample.txt"
    original_content = sample_path.read_text(encoding="utf-8")

    try:
        # Append the extra line
        with open(sample_path, "a", encoding="utf-8") as fh:
            fh.write("This line was added after the baseline!\n")

        cmd_lines = (
            "echo 'This line was added after the baseline!' >> test_data/sample.txt\n"
            "python3 python_tool/file_integrity_checker.py check "
            "--path test_data --baseline baseline.json"
        )
        out = run(
            f"python3 python_tool/file_integrity_checker.py check "
            f"--path test_data --baseline {tmp_baseline}",
            cwd
        )
    finally:
        # Always restore
        sample_path.write_text(original_content, encoding="utf-8")

    render_screenshot(
        title="11 — Python Modified-File Detection",
        command_line="python3 python_tool/file_integrity_checker.py check --path test_data --baseline baseline.json",
        output_text=out,
        filename="11_python_check_modified.png",
        width=960,
    )

    # Clean up temp baseline
    if os.path.exists(tmp_baseline):
        os.remove(tmp_baseline)

    # ------------------------------------------------------------------
    # 12  All Python unit tests passing
    # ------------------------------------------------------------------
    out = run("python3 tests/test_file_integrity_checker.py -v 2>&1", cwd)
    render_screenshot(
        title="12 — All Unit Tests Passing (27/27)",
        command_line="python3 tests/test_file_integrity_checker.py -v",
        output_text=out,
        filename="12_unit_tests.png",
        width=980,
    )

    print("\n✓ All 12 screenshots generated in screenshots/\n")


if __name__ == "__main__":
    main()
