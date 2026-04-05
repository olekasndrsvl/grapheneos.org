#!/usr/bin/env python3
"""
Automatically localize content in HTML files.
Finds dates, numbers, sizes, and durations and replaces them with formatting helper calls.
"""

import re
from pathlib import Path
import argparse

class ContentLocalizer:
    """Automatically localize content in HTML files."""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.stats = {'files_processed': 0, 'replacements': 0}

        # Regular expressions used for matching
        self.patterns = [
            # Dates in Month YYYY format (January 2024, March 2033)
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
             self._replace_date_month_year),

            # Dates in YYYY-MM-DD or YYYY/MM/DD format
            (r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b',
             self._replace_date_iso),

            # Dates in DD Month YYYY format (31 December 2024)
            (r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
             self._replace_date_day_month_year),

            # Sizes in GiB/GB/MB/KB (136GiB, 32GB, 512MB, 64KB)
            (r'\b(\d+(?:\.\d+)?)\s*(GiB|GB|MB|KB|MiB)\b',
             self._replace_size),

            # Prices in USD ($5, $5,000, $1,234.56)
            (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\b',
             self._replace_currency_usd),

            # Numbers with thousands separators (1,234,567) and without
            (r'\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b',
             self._replace_number_with_commas),

            # Years (2024, 2025, 2026), but only when they are not part of other patterns
            (r'\b(19|20)\d{2}\b',
             self._replace_year),

            # Versions (Android 16, Android 15) are intentionally ignored
            # Durations with units (7 years, 5 years, 3 months)
            (r'\b(\d+)\s+(year|years|month|months|day|days|hour|hours)\b',
             self._replace_duration),
        ]

    def _replace_date_month_year(self, match):
        """Replace dates in 'Month YYYY' format."""
        month_name = match.group(1)
        year = match.group(2)
        month_num = self._month_to_number(month_name)
        return f'{{{{ format_date("{year}-{month_num:02d}-01", "MMMM yyyy") }}}}'

    def _replace_date_iso(self, match):
        """Replace dates in YYYY-MM-DD format."""
        year, month, day = match.groups()
        return f'{{{{ format_date("{year}-{month:02d}-{day:02d}", "medium") }}}}'

    def _replace_date_day_month_year(self, match):
        """Replace dates in 'DD Month YYYY' format."""
        day, month_name, year = match.groups()
        month_num = self._month_to_number(month_name)
        return f'{{{{ format_date("{year}-{month_num:02d}-{int(day):02d}", "long") }}}}'

    def _replace_size(self, match):
        """Replace sizes such as 136GiB or 32GB."""
        value = match.group(1)
        unit = match.group(2)

        # Convert the value to bytes for format_size
        multiplier = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3,
                      'GiB': 1024**3, 'MiB': 1024**2, 'KiB': 1024}

        bytes_value = float(value) * multiplier.get(unit, 1)

        # Use zero decimal places for whole numbers
        decimals = 0 if '.' not in value else 1

        return f'{{{{ format_size({int(bytes_value)}, {decimals}) }}}}'

    def _replace_currency_usd(self, match):
        """Replace USD prices such as $5 or $5,000."""
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str)
            # Whole numbers do not need decimal places
            if amount == int(amount):
                return f'{{{{ format_currency({int(amount)}, "USD") }}}}'
            return f'{{{{ format_currency({amount}, "USD") }}}}'
        except Exception:
            return match.group(0)

    def _replace_number_with_commas(self, match):
        """Replace numbers that use thousands separators."""
        num_str = match.group(1).replace(',', '')
        try:
            num = float(num_str)
            if num == int(num):
                return f'{{{{ format_number({int(num)}) }}}}'
            return f'{{{{ format_number({num}) }}}}'
        except Exception:
            return match.group(0)

    def _replace_year(self, match):
        """Replace years with formatted equivalents."""
        year = match.group(0)
        # Years in IDs (#2026032000) or links are skipped by the surrounding context checks
        return f'{{{{ format_number({year}, 0) }}}}'

    def _replace_duration(self, match):
        """Replace durations such as 7 years or 5 months."""
        number = match.group(1)
        unit = match.group(2)

        # Determine the singular and plural forms
        if unit in ['year', 'years']:
            singular = 'year'
            plural = 'years'
        elif unit in ['month', 'months']:
            singular = 'month'
            plural = 'months'
        elif unit in ['day', 'days']:
            singular = 'day'
            plural = 'days'
        elif unit in ['hour', 'hours']:
            singular = 'hour'
            plural = 'hours'
        else:
            return match.group(0)

        return f'{{{{ ngettext("{singular}", "{plural}", {number}) }}}}'

    def _month_to_number(self, month_name):
        """Convert a month name to its numeric value."""
        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        return months.get(month_name, 1)

    def _should_skip_line(self, line):
        """Check whether the line should be skipped."""
        skip_patterns = [
            r'<\s*pre',           # inside pre blocks
            r'<\s*code',          # inside code blocks
            r'<\s*script',        # inside script blocks
            r'id="[^"]*"',        # in id attributes
            r'href="[^"]*"',      # in links
            r'src="[^"]*"',       # in src attributes
            r'{{.*}}',            # already contains templates
            r'{%',                # already contains templates
        ]

        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def process_file(self, filepath):
        """Process a single HTML file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original = content
            lines = content.split('\n')
            modified_lines = []

            in_code_block = False

            for line in lines:
                # Detect the start and end of code blocks
                if '<pre' in line or '<code' in line:
                    in_code_block = True
                elif '</pre>' in line or '</code>' in line:
                    in_code_block = False

                # Skip code blocks
                if in_code_block or self._should_skip_line(line):
                    modified_lines.append(line)
                    continue

                # Apply all replacement patterns
                for pattern, replacer in self.patterns:
                    line = re.sub(pattern, replacer, line, flags=re.IGNORECASE)

                modified_lines.append(line)

            modified_content = '\n'.join(modified_lines)

            if modified_content != original:
                self.stats['replacements'] += 1
                if not self.dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                print(f"  ✓ Modified: {filepath}")
            else:
                print(f"  - Unchanged: {filepath}")

            self.stats['files_processed'] += 1

        except Exception as e:
            print(f"  ✗ Error processing {filepath}: {e}")

    def process_directory(self, directory):
        """Process all HTML files in a directory."""
        directory = Path(directory)
        html_files = list(directory.rglob('*.html'))

        print(f"\nFound {len(html_files)} HTML files to process")
        print("-" * 50)

        for filepath in html_files:
            # Skip files inside language directories
            if any(part in ['en', 'de', 'fr', 'es', 'ru'] for part in filepath.parts):
                continue
            self.process_file(filepath)

    def print_stats(self):
        """Print summary statistics."""
        print("\n" + "=" * 50)
        print("STATISTICS:")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Files modified: {self.stats['replacements']}")


def main():
    parser = argparse.ArgumentParser(
        description='Automatically localize dates, numbers, and currencies in HTML files'
    )
    parser.add_argument('path', help='Path to file or directory')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing files')

    args = parser.parse_args()

    localizer = ContentLocalizer(dry_run=args.dry_run)

    path = Path(args.path)
    if path.is_file():
        localizer.process_file(path)
    elif path.is_dir():
        localizer.process_directory(path)
    else:
        print(f"Error: {path} does not exist")
        return

    localizer.print_stats()


if __name__ == '__main__':
    main()
