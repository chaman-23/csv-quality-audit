"""Audit CSV structure and configured data-quality rules; never change the input."""
import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

def validate_contract(contract, fields):
    if not isinstance(contract, dict) or set(contract) - {'required', 'unique', 'numeric'}:
        raise ValueError('Contract must contain only required, unique and numeric rules.')
    for rule in ('required', 'unique', 'numeric'):
        values = contract.get(rule, [])
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(f'{rule} must be a list of column names.')
        missing = set(values) - set(fields)
        if missing:
            raise ValueError(f'{rule}: unknown columns: {sorted(missing)}')

def audit(path, contract):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream, strict=True)
        fields = next(reader, None)
        if not fields or any(not f.strip() for f in fields) or len(fields) != len(set(fields)):
            raise ValueError('CSV must have non-empty, unique column headers.')
        validate_contract(contract, fields)
        missing = Counter()
        numeric = Counter()
        unique = {key: set() for key in contract.get('unique', [])}
        duplicates = Counter()
        seen_rows = set()
        duplicate_rows = 0
        malformed = []
        rows = 0
        valid_rows = 0
        for line, values in enumerate(reader, 2):
            rows += 1
            if len(values) != len(fields):
                malformed.append(line)
                continue
            valid_rows += 1
            values = [v.strip() for v in values]
            row_key = tuple(values)
            duplicate_rows += int(row_key in seen_rows)
            seen_rows.add(row_key)
            row = dict(zip(fields, values))
            for field, value in row.items():
                if not value:
                    missing[field] += 1
            for field in contract.get('numeric', []):
                if not row[field]:
                    continue
                try:
                    valid_number = Decimal(row[field]).is_finite()
                except InvalidOperation:
                    valid_number = False
                if not valid_number:
                    numeric[field] += 1
            for field, seen in unique.items():
                value = row[field]
                if not value:
                    continue
                duplicates[field] += int(value in seen)
                seen.add(value)
        required_missing = {f: missing[f] for f in contract.get('required', []) if missing[f]}
        unique_violations = {f: count for f, count in duplicates.items() if count}
        passed = bool(valid_rows) and not (malformed or duplicate_rows or required_missing or numeric or unique_violations)
        return {'passed': passed, 'rows': rows, 'valid_width_rows': valid_rows,
            'columns': fields, 'duplicate_rows_beyond_first': duplicate_rows,
            'malformed_record_numbers': malformed,
            'missing_by_column': {f: missing[f] for f in fields},
            'required_missing': required_missing, 'invalid_numeric': dict(numeric),
            'duplicate_unique_values_beyond_first': unique_violations}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path('reports/quality-report.json'))
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding='utf-8'))
        report = audit(args.csv_file, contract)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, csv.Error) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(f"{'PASS' if report['passed'] else 'FAIL'}: {report['rows']} records; saved {args.out}")
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__':
    main()
