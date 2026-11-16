import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/geoscience-paper-writing/scripts/zotero_catalog.py'
spec = importlib.util.spec_from_file_location('catalog', SCRIPT)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

def col(key, name, parent=False):
    return {'key': key, 'data': {'name': name, 'parentCollection': parent}}

def item(key, title, lang, abstract=''):
    return {'key': key, 'data': {'itemType': 'journalArticle', 'title': title, 'language': lang,
                                 'date': '2020', 'creators': [], 'abstractNote': abstract}}

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.original_pages = catalog.pages
        self.collections = [col('ROOT0001', 'Papers'), col('OUTS0001', 'Other'),
                            col('SAME0001', 'Shared', 'ROOT0001'), col('SAME0002', 'Shared', 'ROOT0001'),
                            col('NEST0001', 'English', 'SAME0001'), col('SAME0003', 'Shared', 'OUTS0001')]
        data = {'/collections': self.collections,
                '/collections/SAME0001/items/top': [item('ITEM0001', '页岩', 'en', 'abstract text')],
                '/collections/NEST0001/items/top': [item('ITEM0002', 'NMR rock', '', 'other abstract')],
                '/collections/SAME0002/items/top': [item('ITEM0002', 'NMR rock', '', 'other abstract')]}
        catalog.pages = lambda path: data.get(path, [])
        self.cfg = {'root': 'Papers', 'groups': {'sedimentary': [{'name': 'Shared', 'key': 'SAME0001'}],
                    'geophysics': [{'name': 'Shared', 'key': 'SAME0002'}], 'unconventional': []}}

    def tearDown(self):
        catalog.pages = self.original_pages

    def test_nested_cross_domain_and_privacy(self):
        result = catalog.build_catalog(self.cfg)
        self.assertEqual(result['summary']['unique_items'], 2)
        records = {r['key']: r for r in result['items']}
        self.assertEqual(records['ITEM0002']['domains'], ['sedimentary', 'geophysics'])
        self.assertEqual(records['ITEM0002']['language_source'], 'title-latin-inferred')
        self.assertTrue(records['ITEM0001']['language_conflict'])
        self.assertNotIn('abstract', records['ITEM0001'])
        with_abstracts = catalog.build_catalog(self.cfg, True)
        self.assertIn('abstract', with_abstracts['items'][0])
        self.assertEqual(catalog.search(result, 'NMR', 'geophysics', 'en', 3, False)['matches'], 1)

    def test_same_names_require_key(self):
        self.cfg['groups']['sedimentary'] = ['Shared']
        with self.assertRaisesRegex(ValueError, 'explicit collection key'):
            catalog.build_catalog(self.cfg)

    def test_refresh_failure_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            catalog.atomic_write(path, {'old': True})
            before = path.read_bytes()
            self.cfg['groups']['sedimentary'] = ['Missing']
            with self.assertRaises(ValueError):
                result = catalog.build_catalog(self.cfg)
                catalog.atomic_write(path, result)
            self.assertEqual(path.read_bytes(), before)

if __name__ == '__main__':
    unittest.main()
