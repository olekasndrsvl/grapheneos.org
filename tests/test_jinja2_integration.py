#!/usr/bin/env python3
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2i18n import create_i18n_environment


class TestJinja2Integration:
    def test_create_environment_default(self):
        env = create_i18n_environment()
        assert env is not None
        assert env['get_lang']() == 'en'
    
    def test_create_environment_ru(self):
        env = create_i18n_environment('ru')
        assert env['get_lang']() == 'ru'
    
    def test_create_environment_de(self):
        env = create_i18n_environment('de')
        assert env['get_lang']() == 'de'
    
    def test_translation_filter(self):
        env = create_i18n_environment('en')
        result = env['_']('nav.home')
        assert result == 'Home'
    
    def test_translation_filter_ru(self):
        env = create_i18n_environment('ru')
        result = env['_']('nav.home')
        assert result == 'Главная'
    
    def test_translation_filter_missing_key(self):
        env = create_i18n_environment('en')
        result = env['_']('nonexistent.key')
        assert result == 'nonexistent.key'
    
    def test_date_filter(self):
        env = create_i18n_environment('en')
        result = env['datenl']('2024-01-15')
        assert '2024' in result
    
    def test_date_filter_ru(self):
        env = create_i18n_environment('ru')
        result = env['datenl']('2024-01-15')
        assert '2024' in result
    
    def test_number_filter(self):
        env = create_i18n_environment('en')
        result = env['numberl'](1234.56, 2)
        assert '1' in result
    
    def test_currency_filter(self):
        env = create_i18n_environment('en')
        result = env['currencyl'](99.99, 'USD')
        assert '$' in result or '99' in result
    
    def test_get_languages_function(self):
        env = create_i18n_environment('en')
        langs = env['get_languages']()
        assert 'en' in langs
        assert 'ru' in langs
        assert 'de' in langs
    
    def test_get_current_language(self):
        env = create_i18n_environment('ru')
        lang = env['get_current_language']()
        assert lang['code'] == 'ru'
    
    def test_seo_tags_generation(self):
        env = create_i18n_environment('en')
        seo_tags = env['generate_seo_tags']('/index')
        assert 'canonical' in seo_tags or 'hreflang' in seo_tags


class TestJinja2Filters:
    def test_all_languages_render(self):
        for lang in ['en', 'ru', 'de', 'fr', 'es']:
            env = create_i18n_environment(lang)
            assert env is not None
            assert env['get_lang']() == lang


class TestI18nObject:
    def test_i18n_object_accessible(self):
        env = create_i18n_environment('en')
        i18n = env['i18n']
        assert i18n.lang == 'en'
    
    def test_i18n_object_translate(self):
        env = create_i18n_environment('ru')
        i18n = env['i18n']
        result = i18n._('nav.home')
        assert result == 'Главная'
    
    def test_i18n_object_ru(self):
        env = create_i18n_environment('ru')
        i18n = env['i18n']
        assert i18n.lang == 'ru'


class TestSeoTags:
    def test_seo_tags_en(self):
        env = create_i18n_environment('en')
        tags = env['generate_seo_tags']('/features')
        assert 'canonical' in tags
        assert 'hreflang="en"' in tags
    
    def test_seo_tags_ru(self):
        env = create_i18n_environment('ru')
        tags = env['generate_seo_tags']('/features')
        assert 'hreflang="ru"' in tags
    
    def test_seo_tags_all_languages(self):
        env = create_i18n_environment('de')
        tags = env['generate_seo_tags']('/index')
        for lang in ['en', 'de', 'fr', 'es', 'ru']:
            assert f'hreflang="{lang}"' in tags
