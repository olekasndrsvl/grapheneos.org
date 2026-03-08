#!/usr/bin/env python3

import json
import locale
from pathlib import Path
from functools import lru_cache

LOCALE_MAP = {
    'en': 'en_US',
    'de': 'de_DE',
    'fr': 'fr_FR',
    'es': 'es_ES',
    'ru': 'ru_RU',
}

LANGUAGES = {
    'en': 'English',
    'de': 'Deutsch',
    'fr': 'Français',
    'es': 'Español',
    'ru': 'Русский',
}

DEFAULT_LANG = 'en'


class I18n:
    def __init__(self, lang=DEFAULT_LANG):
        self.lang = lang
        self.translations = {}
        self.base_translations = {}
        self.load_translations()
    
    def load_translations(self):
        i18n_dir = Path(__file__).parent / 'i18n'
        
        # Load base translations (English)
        base_file = i18n_dir / 'en' / 'messages.json'
        if base_file.exists():
            with open(base_file, 'r', encoding='utf-8') as f:
                self.base_translations = json.load(f)
        
        # Load current language translations
        if self.lang != 'en':
            lang_file = i18n_dir / self.lang / 'messages.json'
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            else:
                self.translations = {}
    
    def get(self, key, default=None):
        # Try current language
        keys = key.split('.')
        value = self.translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        if value is not None:
            return value
        
        # Fallback to English
        value = self.base_translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        if value is not None:
            return value
        
        return default or key
    
    def _(self, key):
        return self.get(key, key)
    
    def datenl(self, date_str, format_str=None):
        """Format date for locale."""
        if not date_str:
            return ''
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('/', '-'))
        except:
            dt = None
        
        if dt is None:
            return date_str
        
        locale_code = LOCALE_MAP.get(self.lang, 'en_US')
        
        try:
            locale.setlocale(locale.LC_TIME, locale_code)
        except:
            locale.setlocale(locale.LC_TIME, 'en_US')
        
        if format_str:
            return dt.strftime(format_str)
        
        # Default format based on locale
        formats = {
            'en': '%B %d, %Y',
            'de': '%d. %B %Y',
            'fr': '%d %B %Y',
            'es': '%d de %B de %Y',
            'ru': '%d %B %Y',
        }
        fmt = formats.get(self.lang, '%B %d, %Y')
        return dt.strftime(fmt)
    
    def numberl(self, num, decimals=0):
        """Format number for locale."""
        locale_code = LOCALE_MAP.get(self.lang, 'en_US')
        
        try:
            locale.setlocale(locale.LC_NUMERIC, locale_code)
        except:
            locale.setlocale(locale.LC_NUMERIC, 'en_US')
        
        try:
            n = float(num)
            return locale.format_string(f'%.{decimals}f', n, grouping=True)
        except:
            return str(num)
    
    def currencyl(self, amount, currency='USD'):
        """Format currency for locale."""
        locale_code = LOCALE_MAP.get(self.lang, 'en_US')
        
        try:
            locale.setlocale(locale.LC_ALL, locale_code)
        except:
            locale.setlocale(locale.LC_ALL, 'en_US')
        
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'RUB': '₽',
        }
        
        symbol = symbols.get(currency, currency)
        
        try:
            n = float(amount)
            return f'{symbol}{n:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return f'{symbol}{amount}'


def create_i18n_environment(lang=DEFAULT_LANG):
    """Create Jinja2 environment with i18n filters."""
    from jinja2 import Environment, FileSystemLoader
    
    i18n = I18n(lang)
    
    # Create filters
    def _(key):
        return i18n._(key)
    
    def datenl(date_str, format_str=None):
        return i18n.datenl(date_str, format_str)
    
    def numberl(num, decimals=0):
        return i18n.numberl(num, decimals)
    
    def currencyl(amount, currency='USD'):
        return i18n.currencyl(amount, currency)
    
    def get_lang():
        return lang
    
    def get_languages():
        return LANGUAGES
    
    def get_current_language():
        return {'code': lang, 'name': LANGUAGES.get(lang, lang)}
    
    def generate_seo_tags(current_page):
        """Generate canonical URL and hreflang tags for i18n."""
        base_url = "https://grapheneos.org"
        languages = ['en', 'de', 'fr', 'es', 'ru']
        
        # Determine the page path (without leading slash and lang prefix)
        page_path = current_page.lstrip('/')
        
        tags = []
        
        # Canonical URL - always points to base language (en) or current lang version
        current_lang = lang
        if current_lang == 'en':
            canonical_url = f"{base_url}/{page_path}" if page_path else base_url + "/"
        else:
            canonical_url = f"{base_url}/{page_path}" if page_path else f"{base_url}/{current_lang}/"
        
        tags.append(f'<link rel="canonical" href="{canonical_url}"/>')
        
        # hreflang tags for all languages
        for lang_code in languages:
            if lang_code == 'en':
                hreflang_url = f"{base_url}/{page_path}" if page_path else base_url + "/"
            else:
                hreflang_url = f"{base_url}/{lang_code}/{page_path}" if page_path else f"{base_url}/{lang_code}/"
            
            tags.append(f'<link rel="alternate" hreflang="{lang_code}" href="{hreflang_url}"/>')
        
        # x-default
        x_default = f"{base_url}/{page_path}" if page_path else base_url + "/"
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{x_default}"/>')
        
        return '\n'.join(tags)
    
    def get_page_url():
        """Get the current page URL."""
        return "https://grapheneos.org"
    
    return {
        'i18n': i18n,
        '_': _,
        'datenl': datenl,
        'numberl': numberl,
        'currencyl': currencyl,
        'get_lang': get_lang,
        'get_languages': get_languages,
        'get_current_language': get_current_language,
        'generate_seo_tags': generate_seo_tags,
        'get_page_url': get_page_url,
    }


def get_supported_languages():
    """Return list of supported language codes."""
    return list(LANGUAGES.keys())


if __name__ == '__main__':
    # Test
    i18n = I18n('ru')
    print(i18n._('app_name'))
    print(i18n._('nav.features'))
    print(i18n.datenl('2024-01-15'))
    print(i18n.numberl(1234.56))
    print(i18n.currencyl(99.99, 'USD'))
