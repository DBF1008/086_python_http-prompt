# -*- coding: utf-8 -*-
import unittest

from prompt_toolkit.document import Document

from http_prompt.completer import HttpPromptCompleter
from http_prompt.context import Context


class TestCompleter(unittest.TestCase):

    def setUp(self):
        self.context = Context('http://localhost', spec={
            'paths': {
                '/users': {},
                '/users/{username}': {},
                '/users/{username}/events': {},
                '/users/{username}/orgs': {},
                '/orgs': {},
                '/orgs/{org}': {},
                '/orgs/{org}/events': {},
                '/orgs/{org}/members': {}
            }
        })
        self.completer = HttpPromptCompleter(self.context)
        self.completer_event = None

    def get_completions(self, command):
        if not isinstance(command, str):
            command = command.decode()
        position = len(command)
        completions = self.completer.get_completions(
            Document(text=command, cursor_position=position),
            self.completer_event)
        return [c.text for c in completions]

    def test_header_name(self):
        result = self.get_completions('ctype')
        self.assertEqual(result[0], 'Content-Type')

    def test_header_value(self):
        result = self.get_completions('Content-Type:json')
        self.assertEqual(result[0], 'application/json')

    def test_verify_option(self):
        result = self.get_completions('--vfy')
        self.assertEqual(result[0], '--verify')

    def test_preview_then_action(self):
        result = self.get_completions('httpie po')
        self.assertEqual(result[0], 'post')

    def test_rm_body_param(self):
        self.context.body_params['my_name'] = 'dont_care'
        result = self.get_completions('rm -b ')
        self.assertEqual(result[0], 'my_name')

    def test_rm_body_json_param(self):
        self.context.body_json_params['number'] = 2
        result = self.get_completions('rm -b ')
        self.assertEqual(result[0], 'number')

    def test_rm_querystring_param(self):
        self.context.querystring_params['my_name'] = 'dont_care'
        result = self.get_completions('rm -q ')
        self.assertEqual(result[0], 'my_name')

    def test_rm_header(self):
        self.context.headers['Accept'] = 'dont_care'
        result = self.get_completions('rm -h ')
        self.assertEqual(result[0], 'Accept')

    def test_rm_option(self):
        self.context.options['--form'] = None
        result = self.get_completions('rm -o ')
        self.assertEqual(result[0], '--form')

    def test_querystring_with_chinese(self):
        result = self.get_completions('name==王')
        self.assertFalse(result)

    def test_header_with_spanish(self):
        result = self.get_completions('X-Custom-Header:Jesú')
        self.assertFalse(result)

    def test_options_method(self):
        result = self.get_completions('opt')
        self.assertEqual(result[0], 'options')

    def test_ls_no_path(self):
        result = self.get_completions('ls ')
        self.assertEqual(result, ['orgs', 'users'])

    def test_ls_no_path_substring(self):
        result = self.get_completions('ls o')
        self.assertEqual(result, ['orgs'])

    def test_ls_absolute_path(self):
        result = self.get_completions('ls /users/1/')
        self.assertEqual(result, ['events', 'orgs'])

    def test_ls_absolute_path_substring(self):
        result = self.get_completions('ls /users/1/e')
        self.assertEqual(result, ['events'])

    def test_ls_relative_path(self):
        self.context.url = 'http://localhost/orgs'
        result = self.get_completions('ls 1/')
        self.assertEqual(result, ['events', 'members'])

    def test_cd_no_path(self):
        result = self.get_completions('cd ')
        self.assertEqual(result, ['orgs', 'users'])

    def test_cd_no_path_substring(self):
        result = self.get_completions('cd o')
        self.assertEqual(result, ['orgs'])

    def test_cd_absolute_path(self):
        result = self.get_completions('cd /users/1/')
        self.assertEqual(result, ['events', 'orgs'])

    def test_cd_absolute_path_substring(self):
        result = self.get_completions('cd /users/1/e')
        self.assertEqual(result, ['events'])

    def test_cd_relative_path(self):
        self.context.url = 'http://localhost/orgs'
        result = self.get_completions('cd 1/')
        self.assertEqual(result, ['events', 'members'])


class TestSpecParamCompleter(unittest.TestCase):

    def setUp(self):
        self.context = Context('http://localhost', spec={
            'paths': {
                '/items': {
                    'parameters': [
                        {'name': 'shared', 'in': 'query'},
                    ],
                    'get': {
                        'parameters': [
                            {'name': 'limit', 'in': 'query'},
                            {'name': 'offset', 'in': 'query'},
                        ]
                    },
                    'post': {
                        'parameters': [
                            {'name': 'name', 'in': 'body'},
                        ]
                    }
                },
                '/users': {},
            }
        })
        self.context.url = 'http://localhost/items'
        self.completer = HttpPromptCompleter(self.context)
        self.completer_event = None

    def get_completions(self, command):
        position = len(command)
        completions = self.completer.get_completions(
            Document(text=command, cursor_position=position),
            self.completer_event)
        return [c.text for c in completions]

    def test_get_shows_get_params(self):
        result = self.get_completions('get ')
        self.assertIn('limit', result)
        self.assertIn('offset', result)
        self.assertIn('shared', result)
        self.assertNotIn('name', result)

    def test_post_shows_post_params(self):
        result = self.get_completions('post ')
        self.assertIn('name', result)
        self.assertIn('shared', result)
        self.assertNotIn('limit', result)
        self.assertNotIn('offset', result)

    def test_shared_params_in_all_methods(self):
        result_get = self.get_completions('get ')
        result_post = self.get_completions('post ')
        self.assertIn('shared', result_get)
        self.assertIn('shared', result_post)

    def test_no_spec_no_spec_params(self):
        """Without a spec, no spec parameters should appear."""
        ctx = Context('http://localhost')
        completer = HttpPromptCompleter(ctx)
        result = [c.text for c in completer.get_completions(
            Document(text='get ', cursor_position=4),
            self.completer_event)]
        self.assertNotIn('limit', result)
        self.assertNotIn('shared', result)

    def test_spec_params_coexist_with_context_params(self):
        """User-set params and spec params should both appear."""
        self.context.body_params['my_field'] = 'val'
        result = self.get_completions('post ')
        self.assertIn('my_field', result)
        self.assertIn('name', result)
        self.assertIn('shared', result)

    def test_ls_still_shows_all_params(self):
        """ls should show directories only, not be affected by method filter."""
        self.context.url = 'http://localhost'
        result = self.get_completions('ls ')
        self.assertIn('items', result)
        self.assertIn('users', result)

    def test_cd_unaffected(self):
        """cd completion should still work normally."""
        self.context.url = 'http://localhost'
        result = self.get_completions('cd ')
        self.assertIn('items', result)
        self.assertIn('users', result)
