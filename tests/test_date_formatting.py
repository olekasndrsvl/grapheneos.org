#!/usr/bin/env python3
import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2i18n import I18n


class TestDateFormatting:
    def test_date_format_en(self):
        i18n = I18n('en')
        result = i18n.datenl('2024-03-15')
        assert 'March' in result or '15' in result
    
    def test_date_format_ru(self):
        i18n = I18n('ru')
        result = i18n.datenl('2024-03-15')
        assert 'марта' in result.lower() or '15' in result
    
    def test_date_format_de(self):
        i18n = I18n('de')
        result = i18n.datenl('2024-03-15')
        assert 'märz' in result.lower() or '15' in result
    
    def test_date_format_fr(self):
        i18n = I18n('fr')
        result = i18n.datenl('2024-03-15')
        assert 'mars' in result.lower() or '15' in result
    
    def test_date_format_es(self):
        i18n = I18n('es')
        result = i18n.datenl('2024-03-15')
        assert 'marzo' in result.lower() or '15' in result
    
    def test_custom_date_format(self):
        i18n = I18n('en')
        result = i18n.datenl('2024-03-15', '%Y-%m-%d')
        assert result == '2024-03-15'
    
    def test_invalid_date(self):
        i18n = I18n('en')
        result = i18n.datenl('not a date')
        assert result == 'not a date'
    
    def test_empty_date(self):
        i18n = I18n('en')
        assert i18n.datenl('') == ''
    
    @pytest.mark.parametrize("lang", ['en', 'ru', 'de', 'fr', 'es'])
    def test_all_languages(self, lang):
        i18n = I18n(lang)
        result = i18n.datenl('2024-03-15')
        assert '2024' in result
