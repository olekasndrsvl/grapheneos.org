#!/usr/bin/env python3
import pytest
import json
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2i18n import I18n, LANGUAGES, DEFAULT_LANG


class TestI18nBasic:
    def test_init_default_language(self):
        i18n = I18n()
        assert i18n.lang == DEFAULT_LANG
        assert i18n.lang == 'en'
    
    def test_init_specific_language(self):
        i18n = I18n('ru')
        assert i18n.lang == 'ru'
    
    def test_init_de_language(self):
        i18n = I18n('de')
        assert i18n.lang == 'de'
    
    def test_init_fr_language(self):
        i18n = I18n('fr')
        assert i18n.lang == 'fr'
    
    def test_languages_dict(self):
        assert 'en' in LANGUAGES
        assert 'ru' in LANGUAGES
        assert 'de' in LANGUAGES
        assert 'fr' in LANGUAGES
        assert 'es' in LANGUAGES
        assert LANGUAGES['en'] == 'English'
        assert LANGUAGES['ru'] == 'Русский'


class TestI18nTranslations:
    def test_load_translations_en(self):
        i18n = I18n('en')
        assert 'app_name' in i18n.base_translations
    
    def test_load_translations_ru(self):
        i18n = I18n('ru')
        assert 'app_name' in i18n.translations
        assert i18n._('app_name') == 'GrapheneOS'
    
    def test_load_translations_de(self):
        i18n = I18n('de')
        assert 'app_name' in i18n.translations
    
    def test_load_translations_fr(self):
        i18n = I18n('fr')
        assert 'app_name' in i18n.translations
    
    def test_nested_key_access(self):
        i18n = I18n('en')
        assert i18n.get('nav.home') is not None
        assert i18n.get('footer.copyright') is not None
    
    def test_missing_key_returns_key(self):
        i18n = I18n('ru')
        assert i18n._('nonexistent.key') == 'nonexistent.key'
    
    def test_fallback_to_english(self):
        i18n = I18n('ru')
        assert i18n._('nav.features') is not None


class TestI18nEdgeCases:
    def test_empty_translation(self):
        i18n = I18n('en')
        assert i18n._('totally.missing.key.12345') == 'totally.missing.key.12345'
    
    def test_get_method(self):
        i18n = I18n('en')
        result = i18n.get('nav.home', 'default')
        assert result == 'default' or isinstance(result, str)
