# -*- coding: utf-8 -*-
from .base import TempAppDirTestCase
from http_prompt.context import Context
from http_prompt.contextio import save_context, load_context


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

    def test_save_and_load_multi_value_querystring(self):
        """Duplicate query params must survive a save/load round-trip."""
        c = Context('http://localhost/api')
        c.querystring_params['name'] = ['alice', 'bob']
        c.querystring_params['tag'] = ['x', 'y', 'z']
        c.querystring_params['page'] = ['1']
        save_context(c)

        c2 = Context('http://0.0.0.0')
        load_context(c2)

        self.assertEqual(c2.url, 'http://localhost/api')
        self.assertEqual(c2.querystring_params, {
            'name': ['alice', 'bob'],
            'tag': ['x', 'y', 'z'],
            'page': ['1']
        })

    def test_save_and_load_mixed_request_items(self):
        """All item types (qs, json body, form body, headers) round-trip."""
        c = Context('http://localhost:8000/v2')
        c.querystring_params['color'] = ['red', 'blue']
        c.querystring_params['limit'] = ['10']
        c.body_json_params['enabled'] = True
        c.body_json_params['items'] = ['foo', 'bar']
        c.body_params['username'] = 'jane'
        c.headers['Accept'] = 'application/json'
        c.headers['Authorization'] = 'Bearer tok123'
        c.options['--verify'] = 'no'
        c.options['--form'] = None
        save_context(c)

        c2 = Context('http://0.0.0.0')
        load_context(c2)

        self.assertEqual(c2.url, 'http://localhost:8000/v2')
        self.assertEqual(c2.querystring_params, {
            'color': ['red', 'blue'],
            'limit': ['10']
        })
        self.assertEqual(c2.body_json_params, {
            'enabled': True,
            'items': ['foo', 'bar']
        })
        self.assertEqual(c2.body_params, {'username': 'jane'})
        self.assertEqual(c2.headers, {
            'Accept': 'application/json',
            'Authorization': 'Bearer tok123'
        })
        self.assertEqual(c2.options, {
            '--verify': 'no',
            '--form': None
        })

    def test_save_excludes_style_option(self):
        """The --style option must not be persisted to disk."""
        c = Context('http://localhost')
        c.options['--style'] = 'monokai'
        c.options['--verify'] = 'no'
        c.headers['Accept'] = 'text/html'
        save_context(c)

        c2 = Context('http://0.0.0.0')
        load_context(c2)

        self.assertNotIn('--style', c2.options)
        self.assertEqual(c2.options, {'--verify': 'no'})
        self.assertEqual(c2.headers, {'Accept': 'text/html'})

    def test_save_and_load_roundtrip_stability(self):
        """Two consecutive save/load cycles produce identical contexts."""
        c = Context('http://localhost/api')
        c.querystring_params['q'] = ['a', 'b', 'c']
        c.body_json_params['nested'] = {'key': [1, 2]}
        c.body_params['field'] = 'value'
        c.headers['X-Custom'] = 'test'
        c.options['--verbose'] = None
        save_context(c)

        c2 = Context('http://0.0.0.0')
        load_context(c2)
        save_context(c2)

        c3 = Context('http://0.0.0.0')
        load_context(c3)

        self.assertEqual(c2, c3)
