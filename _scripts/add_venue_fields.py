#!/usr/bin/env python3
"""
Parse publication description strings and add structured venue fields to YAML frontmatter.
Adds: journal, volume, issue, pages, article-number, conference, book-title, editors,
      publisher, institution, series.
Keeps original 'description' field untouched as fallback.
"""
import os, re, sys

PUBS_DIR = os.path.join(os.path.dirname(__file__), '..', 'publications')

def parse_journal(desc):
    """Parse 'Journal Name, Vol(Issue), Pages' patterns."""
    fields = {}
    # Pattern: "Journal Name, Vol(Issue), Pages"
    m = re.match(r'^(.+?),\s*(\d+)\(([^)]+)\),\s*(.+)$', desc)
    if m:
        fields['journal'] = m.group(1).strip()
        fields['volume'] = m.group(2)
        fields['issue'] = m.group(3)
        pages = m.group(4).strip()
        # Detect article number (single number, no dash) vs page range
        if re.match(r'^\d+$', pages) and len(pages) >= 5:
            fields['article-number'] = pages
        else:
            fields['pages'] = pages
        return fields

    # Pattern: "Journal Name, Vol(Issue)" (no pages)
    m = re.match(r'^(.+?),\s*(\d+)\(([^)]+)\)$', desc)
    if m:
        fields['journal'] = m.group(1).strip()
        fields['volume'] = m.group(2)
        fields['issue'] = m.group(3)
        return fields

    # Pattern: "Journal Name, Vol, Pages" (no issue)
    m = re.match(r'^(.+?),\s*(\d+),\s*(.+)$', desc)
    if m:
        name = m.group(1).strip()
        # Avoid matching "In: ..." book chapters
        if not name.startswith('In:'):
            fields['journal'] = name
            fields['volume'] = m.group(2)
            pages = m.group(3).strip()
            if re.match(r'^\d+$', pages) and len(pages) >= 5:
                fields['article-number'] = pages
            else:
                fields['pages'] = pages
            return fields

    return fields


def parse_conference(desc):
    """Parse conference description strings."""
    fields = {}

    # Pattern: "Academy of Management Proceedings YEAR(Issue), Article"
    m = re.match(r'^(Academy of Management (?:Proceedings|Global Proceedings))\s*(\d{4})?\(?(\d)?\)?,?\s*(.+)?$', desc)
    if m:
        fields['conference'] = m.group(1).strip()
        if m.group(2):
            fields['volume'] = m.group(2)
        if m.group(3):
            fields['issue'] = m.group(3)
        if m.group(4):
            article = m.group(4).strip()
            if article:
                fields['article-number'] = article
        return fields

    # Pattern: "Academy of Management Annual Meeting YEAR" or "Xth Annual Meeting of the AoM, AOM YEAR"
    m = re.match(r'^(.*Academy of Management.*?)(?:,\s*(.+))?$', desc)
    if m and 'Proceedings' not in desc:
        fields['conference'] = m.group(1).strip()
        # Only treat as pages if it looks like numbers/page ranges
        if m.group(2) and re.match(r'^\d[\d\-]+$', m.group(2).strip()):
            fields['pages'] = m.group(2).strip()
        return fields

    # Pattern: "Xth Conference Name (ABBR), Pages" or "Conference Name, Pages"
    m = re.match(r'^(.+?),\s*(\d[\d\-]+\d?)$', desc)
    if m:
        fields['conference'] = m.group(1).strip()
        fields['pages'] = m.group(2).strip()
        return fields

    # Plain conference name
    fields['conference'] = desc
    return fields


def parse_book_chapter(desc):
    """Parse book chapter descriptions."""
    fields = {}

    # Pattern: "In: Editors, Book Title, Pages"  or "In: Book Title, Pages"  or "In: Book Title"
    m = re.match(r'^In:\s*(.+)$', desc)
    if m:
        rest = m.group(1).strip()
        # Check for pages at the end: ", 123-456" or ", 123"
        pages_m = re.search(r',\s*(\d+(?:-\d+)?)$', rest)
        if pages_m:
            fields['pages'] = pages_m.group(1)
            rest = rest[:pages_m.start()].strip()

        # Check for editors pattern: "Name & Name, Title" or "Name, Name, Title"
        # Heuristic: if the text before the first comma contains "&" or "et al", it's editors
        parts = rest.split(', ', 1)
        if len(parts) == 2 and ('&' in parts[0] or 'et al' in parts[0]):
            fields['editors'] = parts[0].strip()
            fields['book-title'] = parts[1].strip()
        else:
            fields['book-title'] = rest.strip()
        return fields

    # Pattern: "Series Name, Volume, Pages"
    m = re.match(r'^(.+?),\s*(\d+),\s*(\d+(?:-\d+)?)$', desc)
    if m:
        fields['series'] = m.group(1).strip()
        fields['volume'] = m.group(2)
        fields['pages'] = m.group(3)
        return fields

    # Fallback: just the book title
    if desc and desc != 'Book chapter':
        fields['book-title'] = desc
    return fields


def parse_dissertation(desc):
    """Parse 'Dissertation, University Name'."""
    fields = {}
    m = re.match(r'^Dissertation,\s*(.+)$', desc)
    if m:
        fields['institution'] = m.group(1).strip()
    return fields


def parse_working_paper(desc):
    """Parse working paper descriptions."""
    fields = {}
    if desc in ('Working Paper', 'Discussion Paper', 'SSRN Working Paper'):
        if 'SSRN' in desc:
            fields['institution'] = 'SSRN'
        return fields
    # Institution or venue
    fields['institution'] = desc
    return fields


def parse_book(desc):
    """Parse book (publisher) descriptions."""
    fields = {}
    # May include city: "Publisher, City"
    parts = desc.split(', ')
    fields['publisher'] = parts[0].strip()
    return fields


def parse_report(desc):
    """Parse report descriptions."""
    fields = {}
    fields['publisher'] = desc
    return fields


PARSERS = {
    'journal': parse_journal,
    'conference': parse_conference,
    'book-chapter': parse_book_chapter,
    'dissertation': parse_dissertation,
    'working-paper': parse_working_paper,
    'book': parse_book,
    'report': parse_report,
}


def add_fields_to_frontmatter(content, new_fields):
    """Insert new YAML fields before the closing --- of frontmatter."""
    if not new_fields:
        return content

    # Find the second --- (end of frontmatter)
    m = re.match(r'^(---\n)(.*?\n)(---)', content, re.DOTALL)
    if not m:
        return content

    header = m.group(1)
    body = m.group(2)
    closer = m.group(3)
    rest = content[m.end():]

    # Build YAML lines for new fields
    lines = []
    for key, val in new_fields.items():
        # Quote values that contain special YAML characters
        if any(c in str(val) for c in [':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
            lines.append(f'{key}: "{val}"')
        else:
            lines.append(f'{key}: "{val}"')
    new_yaml = '\n'.join(lines) + '\n'

    return header + body + new_yaml + closer + rest


def process_file(filepath, dry_run=False):
    """Process a single publication .qmd file."""
    with open(filepath) as f:
        content = f.read()

    # Extract pub-type and description
    pt_m = re.search(r'^pub-type:\s*"(.+?)"', content, re.MULTILINE)
    desc_m = re.search(r'^description:\s*"(.+?)"', content, re.MULTILINE)

    if not pt_m or not desc_m:
        return None

    pub_type = pt_m.group(1)
    description = desc_m.group(1)

    parser = PARSERS.get(pub_type)
    if not parser:
        return None

    new_fields = parser(description)
    if not new_fields:
        return None

    if dry_run:
        return new_fields

    new_content = add_fields_to_frontmatter(content, new_fields)
    with open(filepath, 'w') as f:
        f.write(new_content)
    return new_fields


def main():
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("=== DRY RUN — no files will be modified ===\n")

    files = sorted(f for f in os.listdir(PUBS_DIR) if f.endswith('.qmd'))
    total = 0
    for f in files:
        filepath = os.path.join(PUBS_DIR, f)
        result = process_file(filepath, dry_run=dry_run)
        if result:
            total += 1
            fields_str = ', '.join(f'{k}={v}' for k, v in result.items())
            print(f"  {f}: {fields_str}")
        else:
            print(f"  {f}: (no structured fields extracted)")

    print(f"\nProcessed {total}/{len(files)} files")


if __name__ == '__main__':
    main()
