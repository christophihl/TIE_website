#!/usr/bin/env python3
"""
Parse flat author strings and add structured 'authors' array to publication frontmatter.
Maps known TIE team members to their profile directory slugs via 'internal' field.
Keeps original 'author' string as fallback.
"""
import os, re, sys

PUBS_DIR = os.path.join(os.path.dirname(__file__), '..', 'publications')

# Map of author name variations → team directory slug
# Covers exact matches, title-stripped matches, and known publication name variants
NAME_TO_SLUG = {
    # Prof. Ihl
    "Christoph Ihl": "ihl",
    # Current members
    "Oliver Specht": "specht",
    "Olaf Specht": "specht",           # name variant in specht-etal-2025-aom
    "Oliver Mork": "mork",
    "Olaf Mork": "mork",               # name variant
    "Jonas Wilinski": "wilinski",
    "Jan H. Wilinski": "wilinski",      # name variant in specht-etal-2025-aom
    "Jürgen Christopher Thiesen": "thiesen",
    "Julius C. Thiesen": "thiesen",     # name variant in specht-etal-2025-aom
    "Viktoria Boss": "kessler",         # published under maiden name Boss, now Kessler
    "Viktoria Kessler": "kessler",
    # Alumni
    "Jan-Frederik Arnold": "arnold",
    "Georg Barth": "barth",             # published as Georg, profile says Giulio
    "Giulio Barth": "barth",
    "Carolin Brückmann": "brueckmann",
    "Carolin Petra Brückmann": "brueckmann",
    "Michael Engel": "engel",
    "Dimitri Graf": "graf",
    "Daniel Graf": "graf",              # name variant in ihl-graf-2019-aom
    "Jens Heckmann": "heckmann",
    "Jens Eike Heckmann": "heckmann",
    "Matthias Jacobi": "jacobi",
    "Heinz W. Lampe": "lampe",
    "Benjamin Müller": "mueller",
    "Jan Reerink": "reerink",
    "Jan W. Reerink": "reerink",
    "Jan Willem Reerink": "reerink",
    "Joschka Schwarz": "schwarz",
    "Jörg Schwarz": "schwarz",          # name variant in schwarz-ihl-2019-digital
    "Jan Niklas Wick": "wick",
    "Jan N. Wick": "wick",
}


def parse_author_string(author_str):
    """
    Parse a flat author string into a list of structured author dicts.
    Handles bold markers (**name**) and comma-separated names.
    """
    authors = []

    # Handle "et al." suffix
    has_et_al = 'et al.' in author_str
    clean = author_str.replace('et al.', '').strip().rstrip(',').strip()

    # Split by comma, handling cases carefully
    parts = [p.strip() for p in clean.split(',') if p.strip()]

    for part in parts:
        # Check for bold markers (TIE member indicator in current system)
        is_bold = '**' in part
        name = part.replace('**', '').strip()

        if not name:
            continue

        author = {'name': name}

        # Check if this author maps to a team member
        slug = NAME_TO_SLUG.get(name)
        if slug:
            author['internal'] = slug
        elif is_bold:
            # Bold-marked but not in our map — still likely a team member
            # Try fuzzy matching by last name
            last_name = name.split()[-1] if name.split() else ''
            for mapped_name, mapped_slug in NAME_TO_SLUG.items():
                if mapped_name.split()[-1] == last_name and mapped_slug:
                    author['internal'] = mapped_slug
                    break

        authors.append(author)

    return authors


def yaml_escape(val):
    """Escape a value for YAML string output."""
    if any(c in str(val) for c in [':', '"', "'", '#', '{', '}', '[', ']', '&', '*', '?', '|', '>', '!', '%', '@']):
        return '"' + str(val).replace('"', '\\"') + '"'
    return '"' + str(val) + '"'


def format_authors_yaml(authors):
    """Format authors list as YAML array."""
    lines = ['authors:']
    for a in authors:
        lines.append(f'  - name: {yaml_escape(a["name"])}')
        if 'internal' in a:
            lines.append(f'    internal: "{a["internal"]}"')
    return '\n'.join(lines)


def add_authors_to_frontmatter(content, authors_yaml):
    """Insert authors array before the closing --- of frontmatter."""
    m = re.match(r'^(---\n)(.*?\n)(---)', content, re.DOTALL)
    if not m:
        return content

    header = m.group(1)
    body = m.group(2)
    closer = m.group(3)
    rest = content[m.end():]

    return header + body + authors_yaml + '\n' + closer + rest


def process_file(filepath, dry_run=False):
    """Process a single publication .qmd file."""
    with open(filepath) as f:
        content = f.read()

    # Skip if already has authors array
    if re.search(r'^authors:', content, re.MULTILINE):
        return None, 'already has authors'

    # Extract author string
    m = re.search(r'^author:\s*"(.+?)"', content, re.MULTILINE)
    if not m:
        return None, 'no author field'

    author_str = m.group(1)
    authors = parse_author_string(author_str)

    if not authors:
        return None, 'no authors parsed'

    authors_yaml = format_authors_yaml(authors)

    if dry_run:
        return authors, authors_yaml

    new_content = add_authors_to_frontmatter(content, authors_yaml)
    with open(filepath, 'w') as f:
        f.write(new_content)
    return authors, authors_yaml


def main():
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("=== DRY RUN — no files will be modified ===\n")

    files = sorted(f for f in os.listdir(PUBS_DIR) if f.endswith('.qmd'))
    total = 0
    internal_count = 0

    for f in files:
        filepath = os.path.join(PUBS_DIR, f)
        result, info = process_file(filepath, dry_run=dry_run)
        if result is None:
            print(f"  SKIP {f}: {info}")
        else:
            total += 1
            names = []
            for a in result:
                label = a['name']
                if 'internal' in a:
                    label += f" [{a['internal']}]"
                    internal_count += 1
                names.append(label)
            print(f"  {f}: {' | '.join(names)}")

    print(f"\nProcessed {total}/{len(files)} files")
    print(f"Internal (team-linked) authors: {internal_count} instances")


if __name__ == '__main__':
    main()
