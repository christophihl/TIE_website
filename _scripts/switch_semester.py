#!/usr/bin/env python3
"""Switch the current semester across teaching.qmd and index.qmd.

Usage:
    python _scripts/switch_semester.py ST2026
    python _scripts/switch_semester.py WT2026
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_semester(code: str) -> tuple[str, int]:
    """Parse 'ST2026' or 'WT2026' into (term, year)."""
    m = re.fullmatch(r"(ST|WT)(\d{4})", code)
    if not m:
        print(f"Error: Invalid semester code '{code}'. Expected format: ST2026 or WT2026")
        sys.exit(1)
    return m.group(1), int(m.group(2))


def next_semester(term: str, year: int) -> tuple[str, int]:
    """Derive the upcoming semester from the current one."""
    if term == "ST":
        return "WT", year
    else:
        return "ST", year + 1


def semester_label(term: str, year: int) -> str:
    """Human-readable label: 'Summer Term 2026' or 'Winter Term 2026/27'."""
    if term == "ST":
        return f"Summer Term {year}"
    else:
        return f"Winter Term {year}/{(year + 1) % 100:02d}"


def replace_in_file(filepath: Path, replacements: list[tuple[str, str]]) -> list[str]:
    """Apply regex replacements to a file. Returns list of descriptions."""
    text = filepath.read_text()
    changes = []
    for pattern, replacement in replacements:
        new_text, n = re.subn(pattern, replacement, text)
        if n > 0:
            changes.append(f"  {filepath.name}: {pattern!r} → matched {n}x")
            text = new_text
    if changes:
        filepath.write_text(text)
    return changes


def main():
    if len(sys.argv) != 2:
        print("Usage: python _scripts/switch_semester.py <SEMESTER>")
        print("  e.g. python _scripts/switch_semester.py WT2026")
        sys.exit(1)

    current_code = sys.argv[1].upper()
    cur_term, cur_year = parse_semester(current_code)
    up_term, up_year = next_semester(cur_term, cur_year)

    current = f"{cur_term}{cur_year}"
    upcoming = f"{up_term}{up_year}"
    current_label = semester_label(cur_term, cur_year)
    upcoming_label = semester_label(up_term, up_year)

    print(f"Switching to: current={current} ({current_label}), upcoming={upcoming} ({upcoming_label})")
    print()

    teaching = ROOT / "teaching.qmd"
    index = ROOT / "index.qmd"

    all_changes = []

    # teaching.qmd — 4 replacements
    all_changes += replace_in_file(teaching, [
        # Line ~11: current-courses semester filter
        (r'(id: current-courses\n    contents: teaching/courses/\*/index\.qmd\n    include:\n      semester: )"[A-Z]{2}\d{4}"',
         f'\\1"{current}"'),
        # Line ~18: upcoming-courses semester filter
        (r'(id: upcoming-courses\n    contents: teaching/courses/\*/index\.qmd\n    include:\n      semester: )"[A-Z]{2}\d{4}"',
         f'\\1"{upcoming}"'),
        # Line ~51: current semester subheader label
        (r'\[(?:Summer|Winter) Term \d{4}(?:/\d{2})?\]\{\.semester-subheader\}(\s*\n\s*::: \{#current-courses\})',
         f'[{current_label}]{{.semester-subheader}}\\1'),
        # Line ~65: upcoming semester subheader label
        (r'\[(?:Summer|Winter) Term \d{4}(?:/\d{2})?\]\{\.semester-subheader\}(\s*\n\s*::: \{#upcoming-courses\})',
         f'[{upcoming_label}]{{.semester-subheader}}\\1'),
    ])

    # index.qmd — 1 replacement
    all_changes += replace_in_file(index, [
        # Line ~18: current-courses-home semester filter
        (r'(id: current-courses-home\n    contents: teaching/courses/\*/index\.qmd\n    include:\n      semester: )"[A-Z]{2}\d{4}"',
         f'\\1"{current}"'),
    ])

    if all_changes:
        print("Changes made:")
        for c in all_changes:
            print(c)
        print(f"\nDone! Updated {len(all_changes)} location(s).")
    else:
        print("No changes needed — files already match the target semester.")


if __name__ == "__main__":
    main()
