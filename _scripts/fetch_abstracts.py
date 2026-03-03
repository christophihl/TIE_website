#!/usr/bin/env python3
"""
Fetch abstracts from CrossRef API for publications with DOIs but empty abstracts.
CrossRef API is free and returns abstracts for many publications.
Also tries OpenAlex as fallback.
"""
import os, re, sys, json, time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from html import unescape

PUBS_DIR = os.path.join(os.path.dirname(__file__), '..', 'publications')
CROSSREF_API = 'https://api.crossref.org/works/'
OPENALEX_API = 'https://api.openalex.org/works/doi:'
MAILTO = 'ihl@tuhh.de'  # polite pool for CrossRef


def clean_abstract(text):
    """Clean abstract text: strip HTML tags, unescape entities, normalize whitespace."""
    if not text:
        return ''
    # Remove JATS XML tags
    text = re.sub(r'<jats:[^>]+>', '', text)
    text = re.sub(r'</jats:[^>]+>', '', text)
    # Remove other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Escape double quotes for YAML
    text = text.replace('"', '\\"')
    return text


def fetch_crossref(doi):
    """Fetch abstract from CrossRef API."""
    url = f'{CROSSREF_API}{doi}?mailto={MAILTO}'
    req = Request(url, headers={'User-Agent': f'TIE-Website/1.0 (mailto:{MAILTO})'})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            msg = data.get('message', {})
            abstract = msg.get('abstract', '')
            return clean_abstract(abstract)
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as e:
        return ''


def fetch_openalex(doi):
    """Fetch abstract from OpenAlex API as fallback."""
    url = f'{OPENALEX_API}{doi}'
    req = Request(url, headers={'User-Agent': f'TIE-Website/1.0 (mailto:{MAILTO})'})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            # OpenAlex stores abstract as inverted index - reconstruct it
            inv_index = data.get('abstract_inverted_index')
            if inv_index:
                # Reconstruct from inverted index
                word_positions = []
                for word, positions in inv_index.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = ' '.join(w for _, w in word_positions)
                return clean_abstract(abstract)
            return ''
    except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as e:
        return ''


def update_abstract_in_file(filepath, abstract):
    """Replace empty abstract field with fetched abstract."""
    with open(filepath) as f:
        content = f.read()

    # Replace empty abstract
    new_content = re.sub(
        r'^abstract:\s*""',
        f'abstract: "{abstract}"',
        content,
        count=1,
        flags=re.MULTILINE
    )

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False


def main():
    dry_run = '--dry-run' in sys.argv

    # Find publications with DOI but empty abstract
    targets = []
    for f in sorted(os.listdir(PUBS_DIR)):
        if not f.endswith('.qmd'):
            continue
        path = os.path.join(PUBS_DIR, f)
        with open(path) as fh:
            content = fh.read()
        doi_m = re.search(r'^doi:\s*"(.+?)"', content, re.MULTILINE)
        abstract_m = re.search(r'^abstract:\s*"(.*?)"', content, re.MULTILINE)
        if doi_m and doi_m.group(1) and (not abstract_m or not abstract_m.group(1)):
            targets.append((f, path, doi_m.group(1)))

    print(f"Found {len(targets)} publications with DOI but no abstract\n")

    found = 0
    not_found = 0

    for filename, filepath, doi in targets:
        print(f"  {filename} (DOI: {doi})...", end=' ', flush=True)

        # Try CrossRef first
        abstract = fetch_crossref(doi)

        # Fallback to OpenAlex
        if not abstract:
            abstract = fetch_openalex(doi)

        if abstract and len(abstract) > 50:  # Skip very short/garbage abstracts
            found += 1
            preview = abstract[:80] + '...' if len(abstract) > 80 else abstract
            print(f"FOUND ({len(abstract)} chars): {preview}")
            if not dry_run:
                update_abstract_in_file(filepath, abstract)
        else:
            not_found += 1
            print("NOT FOUND")

        time.sleep(0.5)  # Be polite to APIs

    print(f"\nResults: {found} found, {not_found} not found out of {len(targets)} total")


if __name__ == '__main__':
    main()
