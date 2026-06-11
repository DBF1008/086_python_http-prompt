# -*- coding: utf-8 -*-
from .base import TempAppDirTestCase
from http_prompt.context import Context
from http_prompt.contextio import (save_context, load_context, list_profiles,
                                   delete_profile, profile_exists,
                                   _get_profile_filepath, _get_context_filepath)


class TestContextIO(TempAppDirTestCase):

    def test_save_and_load_context_non_ascii(self):
        c = Context('http://localhost')
        c.headers.update({
            'User-Agent': 'Ö',
            'Authorization': '中文'
        })
        save_context(c)

        c = Context('http://0.0.0.0')
        load_context(c)

        self.assertEqual(c.url, 'http://localhost')
        self.assertEqual(c.headers, {
            'User-Agent': 'Ö',
            'Authorization': '中文'
        })


class TestContextIO_profile(TempAppDirTestCase):

    def test_save_context_default_backward_compatible(self):
        """With no profile_name, saves to context.hp as before."""
        c = Context('http://localhost')
        c.headers['Accept'] = 'text/html'
        save_context(c)

        import os
        filepath = _get_context_filepath()
        self.assertTrue(os.path.exists(filepath))
        self.assertIn('context.hp', filepath)

    def test_save_context_to_profile(self):
        c = Context('http://localhost')
        c.profile_name = 'staging'
        c.headers['Accept'] = 'text/csv'
        save_context(c)

        import os
        filepath = _get_profile_filepath('staging')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Accept:text/csv', content)

    def test_load_profile(self):
        c = Context('http://staging.example.com')
        c.profile_name = 'staging'
        c.headers['X-Token'] = 'abc123'
        save_context(c)

        c2 = Context('http://localhost')
        filepath = _get_profile_filepath('staging')
        load_context(c2, filepath)
        self.assertEqual(c2.url, 'http://staging.example.com')
        self.assertEqual(c2.headers['X-Token'], 'abc123')

    def test_list_profiles_empty(self):
        self.assertEqual(list_profiles(), [])

    def test_list_profiles(self):
        c = Context('http://localhost')
        c.profile_name = 'beta'
        save_context(c)

        c.profile_name = 'alpha'
        save_context(c)

        profiles = list_profiles()
        self.assertEqual(profiles, ['alpha', 'beta'])

    def test_delete_profile(self):
        c = Context('http://localhost')
        c.profile_name = 'todelete'
        save_context(c)

        self.assertTrue(profile_exists('todelete'))
        self.assertTrue(delete_profile('todelete'))
        self.assertFalse(profile_exists('todelete'))

    def test_delete_profile_nonexistent(self):
        self.assertFalse(delete_profile('nosuch'))

    def test_profile_exists(self):
        self.assertFalse(profile_exists('foo'))

        c = Context('http://localhost')
        c.profile_name = 'foo'
        save_context(c)

        self.assertTrue(profile_exists('foo'))

    def test_save_and_load_profile_non_ascii(self):
        c = Context('http://localhost')
        c.profile_name = 'unicode'
        c.headers['Authorization'] = '令牌ABC'
        save_context(c)

        c2 = Context('http://0.0.0.0')
        load_context(c2, _get_profile_filepath('unicode'))
        self.assertEqual(c2.headers['Authorization'], '令牌ABC')
