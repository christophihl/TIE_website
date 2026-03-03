#!/usr/bin/env python3
"""
Add ORCID IDs to structured authors arrays in publication frontmatter.
Matches author names to known ORCIDs and inserts orcid field.
"""
import os, re, sys

PUBS_DIR = os.path.join(os.path.dirname(__file__), '..', 'publications')

# Verified ORCID IDs for team members and frequent co-authors
NAME_TO_ORCID = {
    "Christoph Ihl": "0000-0002-0842-5201",
    "Heinz W. Lampe": "0000-0003-1375-236X",
    "Hannes W. Lampe": "0000-0003-1375-236X",
    "Oliver Mork": "0009-0001-0560-0617",
    "Olaf Mork": "0009-0001-0560-0617",
    "Oliver Specht": "0000-0003-4441-6588",
    "Olaf Specht": "0000-0003-4441-6588",
    "Jan Niklas Wick": "0000-0002-3147-4968",
    "Jan N. Wick": "0000-0002-3147-4968",
    "Giulio Barth": "0000-0002-0133-8754",
    "Georg Barth": "0000-0002-0133-8754",
    "Jan Reerink": "0000-0001-6558-5183",
    "Jan W. Reerink": "0000-0001-6558-5183",
    "Jan Willem Reerink": "0000-0001-6558-5183",
    "Jens Heckmann": "0000-0002-3690-6766",
    "Jens Eike Heckmann": "0000-0002-3690-6766",
    "Carolin Brückmann": "0000-0003-2962-1284",
    "Carolin Petra Brückmann": "0000-0003-2962-1284",
    "Matthias Jacobi": "0000-0003-2103-8721",
    "Viktoria Boss": "0000-0001-7937-4926",
    "Viktoria Kessler": "0000-0001-7937-4926",
    "Robin Kleer": "0000-0001-5360-5351",
    "Alexander Vossen": "0000-0002-9266-2022",
}


def process_file(filepath, dry_run=False):
    """Add orcid fields to authors entries in a publication file."""
    with open(filepath) as f:
        content = f.read()

    # Check if file has authors array
    if not re.search(r'^authors:', content, re.MULTILINE):
        return 0

    # Skip if already has any orcid fields
    if re.search(r'^\s+orcid:', content, re.MULTILINE):
        return 0

    changes = 0
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check for author name line: "  - name: "Author Name""
        m = re.match(r'^(\s+- name: ")(.+?)"$', line)
        if m:
            indent = m.group(1)
            name = m.group(2)
            orcid = NAME_TO_ORCID.get(name)

            if orcid:
                # Calculate indent for orcid line (same as "internal:" would be)
                base_indent = ' ' * (len(indent) - len('- name: "'))
                orcid_line = f'{base_indent}  orcid: "{orcid}"'

                # Check if next line is "internal:" - if so, add orcid after it
                if i + 1 < len(lines) and re.match(r'^\s+internal:', lines[i + 1]):
                    new_lines.append(lines[i + 1])  # add internal line
                    new_lines.append(orcid_line)     # add orcid after internal
                    i += 1  # skip the internal line we just added
                else:
                    new_lines.append(orcid_line)  # add orcid right after name

                changes += 1

        i += 1

    if changes > 0 and not dry_run:
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines))

    return changes


def main():
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("=== DRY RUN ===\n")

    files = sorted(f for f in os.listdir(PUBS_DIR) if f.endswith('.qmd'))
    total_files = 0
    total_orcids = 0

    for f in files:
        filepath = os.path.join(PUBS_DIR, f)
        changes = process_file(filepath, dry_run=dry_run)
        if changes > 0:
            total_files += 1
            total_orcids += changes
            print(f"  {f}: +{changes} ORCID(s)")

    print(f"\nAdded {total_orcids} ORCIDs across {total_files} files")


if __name__ == '__main__':
    main()
