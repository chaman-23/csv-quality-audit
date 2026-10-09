import tempfile
import unittest
from pathlib import Path
from audit import audit

class QualityTests(unittest.TestCase):
    def check(self, text, contract):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.csv'
            path.write_text(text, encoding='utf-8')
            return audit(path, contract)

    def test_clean_data_passes(self):
        r = self.check('id,value\n1,2.50\n2,4\n', {'required':['id','value'],'unique':['id'],'numeric':['value']})
        self.assertTrue(r['passed'])

    def test_dirty_sample(self):
        import json
        root = Path(__file__).parent
        r = audit(root / 'data/dirty.csv', json.loads((root / 'contract.json').read_text()))
        self.assertFalse(r['passed'])
        self.assertEqual(r['duplicate_rows_beyond_first'], 1)
        self.assertEqual(r['invalid_numeric'], {'order_total':2})
        self.assertEqual(r['required_missing'], {'region':1})
        self.assertEqual(r['malformed_record_numbers'], [6])

    def test_quoted_comma_and_whitespace(self):
        r = self.check('id,name\n1,"Doe, Jane"\n 1 ,"Doe, Jane"\n', {'unique':['id']})
        self.assertEqual(r['duplicate_rows_beyond_first'], 1)
        self.assertEqual(r['duplicate_unique_values_beyond_first'], {'id':1})

    def test_optional_empty_value_is_allowed(self):
        r = self.check('id,value\n1,\n', {'required':['id'],'numeric':['value']})
        self.assertTrue(r['passed'])

    def test_header_only_fails(self):
        self.assertFalse(self.check('id,value\n', {})['passed'])

    def test_duplicate_header_and_bad_contract_rejected(self):
        with self.assertRaises(ValueError):
            self.check('id,id\n1,2\n', {})
        with self.assertRaises(ValueError):
            self.check('id\n1\n', {'required':['missing']})

if __name__ == '__main__':
    unittest.main()
