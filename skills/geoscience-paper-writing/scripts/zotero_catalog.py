#!/usr/bin/env python3
"""Optional read-only local Zotero index. No library data is shipped with this project."""
import argparse
import collections
import datetime
import html
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path.home() / '.geoscience-writing'
BASE = 'http://127.0.0.1:23119/api/users/0'
DOMAINS = ('sedimentary', 'geophysics', 'unconventional')

def get(path, **params):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(BASE + path + ('?' + query if query else ''),
                                     headers={'Zotero-API-Version': '3'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def pages(path):
    rows, start = [], 0
    while True:
        batch = get(path, start=start, limit=100, format='json')
        if not isinstance(batch, list):
            raise ValueError('Expected a Zotero API list')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
        start += len(batch)

def language(data):
    raw = str(data.get('language', '')).strip().lower()
    title = str(data.get('title', ''))
    cjk = bool(re.search(r'[\u3400-\u9fff]', title))
    zh = raw.startswith(('zh', 'cn', 'chinese', '中文', '汉语'))
    en = raw.startswith(('en', 'english', '英文', '英语'))
    if cjk:
        return 'zh', 'metadata+title' if zh else 'title-cjk', en
    if zh:
        return 'zh', 'metadata', False
    if en:
        return 'en', 'metadata', False
    if not raw and re.search(r'[A-Za-z]{3}', title):
        return 'en', 'title-latin-inferred', False
    return 'unknown', 'unresolved', False

def resolve_collection(candidates, spec, label):
    if isinstance(spec, str):
        name, key = spec, None
    elif isinstance(spec, dict):
        name, key = spec.get('name'), spec.get('key')
    else:
        raise ValueError(f'{label}: expected a name or {{name, key}}')
    matches = [c for c in candidates if (not name or c['data']['name'] == name)
               and (not key or c['key'] == key)]
    if len(matches) != 1:
        raise ValueError(f'{label}: expected one exact match; found {len(matches)}. Set an explicit collection key.')
    return matches[0]

def build_catalog(config, include_abstracts=False):
    groups = config.get('groups', {})
    if set(groups) != set(DOMAINS) or any(not isinstance(groups[d], list) for d in DOMAINS):
        raise ValueError('groups must contain sedimentary, geophysics, unconventional arrays')
    cols = pages('/collections')
    root = resolve_collection(cols, config.get('root'), 'root')
    root_key = root['key']
    by_key = {c['key']: c['data'] for c in cols}
    def descends(key, ancestor):
        seen = set()
        while key and key not in seen:
            if key == ancestor:
                return True
            seen.add(key)
            key = by_key.get(key, {}).get('parentCollection')
        return False
    descendants = [c for c in cols if c['key'] != root_key and descends(c['key'], root_key)]
    records, mapping, counts = {}, {}, {}
    for domain, specs in groups.items():
        for category_spec in specs:
            category = resolve_collection(descendants, category_spec, domain)
            name, ckey = category['data']['name'], category['key']
            mapping.setdefault(domain, []).append({'name': name, 'key': ckey})
            selected = [c['key'] for c in cols if descends(c['key'], ckey)]
            keys = set()
            for collection_key in selected:
                for row in pages('/collections/' + collection_key + '/items/top'):
                    d, key = row['data'], row['key']
                    if d.get('itemType') in {'note', 'attachment', 'annotation'} or d.get('deleted'):
                        continue
                    lang, source, conflict = language(d)
                    authors = [' '.join(filter(None, (c.get('firstName'), c.get('lastName')))) or c.get('name', '')
                               for c in d.get('creators', []) if c.get('creatorType') == 'author']
                    year_match = re.search(r'\b(?:19|20)\d{2}\b', str(d.get('date', '')))
                    rec = {'key': key, 'title': html.unescape(re.sub(r'<[^>]+>', '', d.get('title', ''))),
                           'authors': authors, 'year': year_match.group(0) if year_match else '',
                           'publication': d.get('publicationTitle', '') or d.get('bookTitle', ''),
                           'itemType': d.get('itemType'), 'DOI': d.get('DOI', ''), 'url': d.get('url', ''),
                           'language': lang, 'language_raw': d.get('language', ''), 'language_source': source,
                           'language_conflict': conflict, 'domains': [], 'categories': [],
                           'evidence_level': 'metadata-and-abstract-only' if include_abstracts else 'metadata-only'}
                    if include_abstracts:
                        rec['abstract'] = html.unescape(re.sub(r'<[^>]+>', '', d.get('abstractNote', ''))).strip()
                    existing = records.setdefault(key, rec)
                    if domain not in existing['domains']:
                        existing['domains'].append(domain)
                    category_label = {'name': name, 'key': ckey}
                    if category_label not in existing['categories']:
                        existing['categories'].append(category_label)
                    keys.add(key)
            counts[domain + ':' + ckey] = dict(collections.Counter(records[k]['language'] for k in keys))
    summary = {'captured_at': datetime.datetime.now().astimezone().isoformat(),
               'root': {'name': root['data']['name'], 'key': root_key}, 'mapping': mapping,
               'counts_by_collection': counts, 'unique_items': len(records),
               'counts_by_domain_language': {f'{d}-{lang}': sum(d in r['domains'] and r['language'] == lang for r in records.values())
                                             for d in DOMAINS for lang in ('zh', 'en', 'unknown')},
               'includes_abstracts': include_abstracts}
    return {'summary': summary, 'items': list(records.values())}

def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.catalog-', suffix='.tmp', delete=False) as file:
            tmp = Path(file.name)
            json.dump(obj, file, ensure_ascii=False, indent=2)
            file.write('\n')
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def search(catalog, query, domain, lang, limit, include_abstracts):
    tokens = query.casefold().split()
    results = []
    for item in catalog['items']:
        if domain and domain not in item['domains'] or lang and item['language'] != lang:
            continue
        fields = [item['key'], item['title'], item['DOI'], item['publication'], item.get('abstract', ''),
                  ' '.join(item['authors']), ' '.join(c['name'] for c in item['categories'])]
        text = ' '.join(fields).casefold()
        if not all(t in text for t in tokens):
            continue
        result = dict(item)
        if not include_abstracts:
            result.pop('abstract', None)
        result['metadata_warnings'] = []
        if item['language_conflict']:
            result['metadata_warnings'].append('Title and language field conflict; verify language')
        if item['language_source'] == 'title-latin-inferred':
            result['metadata_warnings'].append('English inferred from Latin title; verify language')
        if item['year'] and int(item['year']) > datetime.date.today().year:
            result['metadata_warnings'].append('Future publication/issue year; verify dates')
        score = sum(8 * (t in item['title'].casefold()) + 3 * (t in ' '.join(c['name'] for c in item['categories']).casefold()) for t in tokens)
        results.append((score, result))
    results.sort(key=lambda x: (x[0], not x[1]['metadata_warnings'], x[1]['year']), reverse=True)
    return {'matches': len(results), 'items': [r for _, r in results[:limit]]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=HOME / 'config.json')
    parser.add_argument('--data', type=Path, default=HOME / 'catalog.json')
    commands = parser.add_subparsers(dest='command', required=True)
    refresh = commands.add_parser('refresh')
    refresh.add_argument('--include-abstracts', action='store_true', help='Store abstracts locally (may be copyrighted)')
    commands.add_parser('inventory')
    find = commands.add_parser('search')
    find.add_argument('query', nargs='?', default='')
    find.add_argument('--domain', choices=DOMAINS)
    find.add_argument('--language', choices=('zh', 'en', 'unknown'))
    find.add_argument('--limit', type=int, default=10)
    find.add_argument('--abstracts', action='store_true', help='Include locally stored abstracts in output')
    item = commands.add_parser('item')
    item.add_argument('key')
    args = parser.parse_args()
    if args.command == 'refresh':
        config = json.loads(args.config.read_text(encoding='utf-8-sig'))
        catalog = build_catalog(config, args.include_abstracts)
        atomic_write(args.data, catalog)
        result = catalog['summary']
    elif args.command == 'item':
        if not re.fullmatch(r'[A-Z0-9]{8}', args.key):
            parser.error('Zotero item key must be eight uppercase letters/digits')
        row = get('/items/' + args.key)
        fields = ('itemType', 'title', 'creators', 'date', 'publicationTitle', 'volume', 'issue', 'pages', 'DOI', 'url', 'language')
        result = {'key': row['key'], 'data': {k: row['data'][k] for k in fields if k in row['data']}}
    else:
        catalog = json.loads(args.data.read_text(encoding='utf-8'))
        if args.command == 'inventory':
            result = catalog['summary']
        else:
            if args.limit < 1:
                parser.error('--limit must be positive')
            result = search(catalog, args.query, args.domain, args.language, args.limit, args.abstracts)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print('Zotero catalog error: ' + str(exc), file=sys.stderr)
        sys.exit(1)
