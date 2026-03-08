#!/usr/bin/env python3
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2i18n import I18n


class TestNumberFormatting:
    def test_number_format_en(self):
        i18n = I18n('en')
        result = i18n.numberl(1234)
        assert '1' in result
    
    def test_number_format_ru(self):
        i18n = I18n('ru')
        result = i18n.numberl(1234.56, 2)
        cleaned = result.replace('\xa0', '').replace(' ', '').replace(',', '')
        assert '123456' in cleaned
    
    def test_number_format_de(self):
        i18n = I18n('de')
        result = i18n.numberl(1234.56, 2)
        cleaned = result.replace('.', '').replace(',', '')
        assert '123456' in cleaned
    
    def test_decimals_parameter(self):
        i18n = I18n('en')
        result = i18n.numberl(1234.5678, 2)
        assert '1' in result
    
    def test_negative_numbers(self):
        i18n = I18n('en')
        result = i18n.numberl(-1234.56)
        assert '-' in result
    
    def test_zero(self):
        i18n = I18n('en')
        result = i18n.numberl(0)
        assert '0' in result


class TestCurrencyFormatting:
    def test_currency_format_en_usd(self):
        i18n = I18n('en')
        result = i18n.currencyl(99.99, 'USD')
        assert '$' in result or '99' in result
    
    def test_currency_format_ru_rub(self):
        i18n = I18n('ru')
        result = i18n.currencyl(99.99, 'RUB')
        assert '99' in result
    
    def test_currency_format_de_eur(self):
        i18n = I18n('de')
        result = i18n.currencyl(99.99, 'EUR')
        assert '99' in result
    
    def test_unknown_currency(self):
        i18n = I18n('en')
        result = i18n.currencyl(99.99, 'XYZ')
        assert '99' in result
    
    @pytest.mark.parametrize("lang,currency", [
        ('en', 'USD'),
        ('ru', 'RUB'),
        ('de', 'EUR'),
    ])
    def test_currency_all_languages(self, lang, currency):
        i18n = I18n(lang)
        result = i18n.currencyl(99.99, currency)
        assert '99' in result
