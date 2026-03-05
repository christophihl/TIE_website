#!/usr/bin/env python3
"""
Reformat all publication index.qmd files to use the profile-page layout
with hero banner, sidebar metadata, and main content area.
"""

import os
import re
import yaml

PUB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "research", "publications")

BANNER = """::: {.page-header style="background-image: url('../../../assets/images/banners/research.jpg');"}
[Research]{.page-header__title}

[&copy; [Anne Gärtner](https://www.gaertner-photo.de)]{.backimage-caption}
:::"""

def parse_qmd(filepath):
    """Parse a .qmd file and return (frontmatter_dict, frontmatter_raw, body)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on YAML delimiters
    match = re.match(r'^---\n(.*?\n)---\n?(.*)', content, re.DOTALL)
    if not match:
        return None, None, content

    fm_raw = match.group(1)
    body = match.group(2).strip()

    # Parse YAML
    try:
        fm = yaml.safe_load(fm_raw)
    except yaml.YAMLError:
        fm = {}

    return fm, fm_raw, body


def build_sidebar(fm):
    """Build the sidebar content from frontmatter."""
    lines = []

    # Image
    image = fm.get('image', '')
    title = fm.get('title', '')
    if image:
        # Truncate alt text if too long
        alt = title[:60] + '...' if len(title) > 60 else title
        lines.append(f'::: {{.profile-sidebar}}')
        lines.append(f'![{alt}]({image}){{.profile-avatar .detail-image}}')
        lines.append('')
    else:
        lines.append('::: {.profile-sidebar}')
        lines.append('')

    # Metadata
    lines.append('::: {.pub-meta}')

    # Pub type
    pub_type = fm.get('pub-type', '')
    type_labels = {
        'journal': 'Journal Article',
        'conference': 'Conference Paper',
        'book': 'Book',
        'chapter': 'Book Chapter',
        'dissertation': 'PhD Thesis',
        'working': 'Working Paper',
        'report': 'Report',
    }
    type_label = type_labels.get(pub_type, pub_type.title() if pub_type else 'Publication')
    lines.append(f'- {{{{< fa file-lines >}}}} {type_label}')

    # Journal/venue
    journal = fm.get('pub-journal', '')
    if journal:
        lines.append(f'- {{{{< fa book >}}}} {journal}')

    # Year
    date = fm.get('date', '')
    if date:
        year = str(date)[:4]
        lines.append(f'- {{{{< fa calendar >}}}} {year}')

    # Volume/Issue/Pages
    vol = fm.get('volume', '')
    issue = fm.get('issue', '')
    pages = fm.get('pages', '')
    if vol:
        vol_str = f'Vol. {vol}'
        if issue:
            vol_str += f'({issue})'
        if pages:
            vol_str += f', pp. {pages}'
        lines.append(f'- {{{{< fa bookmark >}}}} {vol_str}')

    # DOI
    doi = fm.get('doi', '')
    if doi:
        lines.append(f'- {{{{< fa link >}}}} [DOI](https://doi.org/{doi})')

    # PDF
    pdf = fm.get('pdf', '')
    if pdf:
        lines.append(f'- {{{{< fa file-pdf >}}}} [PDF]({pdf})')

    # External URL (for pubs without DOI)
    url = fm.get('url', '')
    if url and not doi:
        lines.append(f'- {{{{< fa arrow-up-right-from-square >}}}} [Link]({url})')

    # Additional pub-links
    pub_links = fm.get('pub-links', [])
    if pub_links:
        for link in pub_links:
            name = link.get('name', 'Link')
            link_url = link.get('url', '')
            if link_url:
                lines.append(f'- {{{{< fa arrow-up-right-from-square >}}}} [{name}]({link_url})')

    lines.append(':::')
    lines.append('')
    lines.append(':::')

    return '\n'.join(lines)


def build_main(fm):
    """Build the main content area from frontmatter."""
    lines = []
    lines.append('::: {.profile-main}')
    lines.append('')

    # Authors section
    authors = fm.get('authors', [])
    if authors:
        lines.append('## Authors')
        lines.append('')
        author_parts = []
        for a in authors:
            name = a.get('name', '')
            internal = a.get('internal', '')
            if internal:
                author_parts.append(f'[{name}](/team/{internal}/)')
            else:
                author_parts.append(name)
        lines.append(', '.join(author_parts))
        lines.append('')

    # Abstract section
    abstract = fm.get('abstract', '')
    if abstract:
        lines.append('## Abstract')
        lines.append('')
        lines.append(abstract)
        lines.append('')

    # Tags section
    tags = fm.get('tags', [])
    if tags:
        lines.append('## Tags')
        lines.append('')
        tag_spans = [f'`{t}`' for t in tags]
        lines.append(' '.join(tag_spans))
        lines.append('')

    # Citation section
    cite = fm.get('cite', '')
    if cite and cite.strip():
        lines.append('## Citation')
        lines.append('')
        lines.append('```bibtex')
        lines.append(cite.strip())
        lines.append('```')
        lines.append('')

    lines.append(':::')

    return '\n'.join(lines)


def build_new_frontmatter(fm_raw):
    """Update the raw frontmatter string to add/change layout fields."""
    lines = fm_raw.split('\n')
    new_lines = []

    # Track what we need to add
    has_page_layout = False
    has_section_divs = False
    has_toc = False
    has_resources = False

    for line in lines:
        stripped = line.strip()

        # Replace page-layout
        if stripped.startswith('page-layout:'):
            new_lines.append('page-layout: custom')
            has_page_layout = True
            continue

        # Replace section-divs
        if stripped.startswith('section-divs:'):
            new_lines.append('section-divs: false')
            has_section_divs = True
            continue

        # Replace toc
        if stripped.startswith('toc:'):
            new_lines.append('toc: false')
            has_toc = True
            continue

        # Skip existing resources lines (we'll add our own)
        if stripped.startswith('resources:'):
            has_resources = True
            # Skip this and any following indented lines
            continue
        if has_resources and (stripped.startswith('-') and line.startswith('  ')):
            continue
        elif has_resources and not stripped.startswith('-'):
            has_resources = False

        new_lines.append(line)

    # Add missing fields before the last line
    additions = []
    if not has_page_layout:
        additions.append('page-layout: custom')
    if not has_section_divs:
        additions.append('section-divs: false')
    if not has_toc:
        additions.append('toc: false')

    # Add resources
    additions.append('resources:')
    additions.append('  - ../../../assets/images/banners/research.jpg')

    # Insert additions before the end
    result = '\n'.join(new_lines)
    if result.endswith('\n'):
        result += '\n'.join(additions) + '\n'
    else:
        result += '\n' + '\n'.join(additions) + '\n'

    return result


def process_publication(dirpath):
    """Process a single publication directory."""
    index_path = os.path.join(dirpath, 'index.qmd')
    if not os.path.exists(index_path):
        return False

    fm, fm_raw, body = parse_qmd(index_path)
    if fm is None:
        return False

    # Build new frontmatter
    new_fm = build_new_frontmatter(fm_raw)

    # Build body
    sidebar = build_sidebar(fm)
    main = build_main(fm)

    new_body = (
        BANNER + "\n\n"
        "::: {.content-section}\n"
        "::: {.content-block}\n"
        "::: {.profile-page}\n\n"
        + sidebar + "\n\n"
        + main + "\n\n"
        ":::\n"
        ":::\n"
        ":::\n"
    )

    # Write file
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write(new_fm)
        f.write('---\n\n')
        f.write(new_body)

    return True


def main():
    count = 0
    errors = []

    for entry in sorted(os.listdir(PUB_DIR)):
        dirpath = os.path.join(PUB_DIR, entry)
        if not os.path.isdir(dirpath):
            continue

        try:
            if process_publication(dirpath):
                count += 1
                print(f"  OK: {entry}")
            else:
                errors.append(f"  SKIP: {entry} (no index.qmd or parse error)")
        except Exception as e:
            errors.append(f"  ERROR: {entry} — {e}")

    print(f"\nProcessed {count} publications")
    if errors:
        print("Errors/Skips:")
        for e in errors:
            print(e)


if __name__ == '__main__':
    main()
