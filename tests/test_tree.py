import unittest

from http_prompt.tree import Node


class TestNode(unittest.TestCase):

    def setUp(self):
        # Make a tree like this:
        #          root
        #     a             h
        #  b     d        i   n
        # c f   e g     k     o
        #             l m p
        self.root = Node('root')
        self.root.add_path('a', 'b', 'c')
        self.root.add_path('a', 'b', 'f')
        self.root.add_path('a', 'd', 'e')
        self.root.add_path('a', 'd', 'g')
        self.root.add_path('h', 'i', 'k', 'l')
        self.root.add_path('h', 'i', 'k', 'm')
        self.root.add_path('h', 'i', 'k', 'p')
        self.root.add_path('h', 'n', 'o')

    def test_illegal_name(self):
        self.assertRaises(ValueError, Node, '.')
        self.assertRaises(ValueError, Node, '..')

    def test_str(self):
        node = Node('my node')
        self.assertEqual(str(node), 'my node')

    def test_cmp_same_type(self):
        a = Node('a', data={'type': 'dir'})
        b = Node('b', data={'type': 'dir'})
        self.assertTrue(a < b)

    def test_cmp_different_type(self):
        a = Node('a', data={'type': 'file'})
        b = Node('b', data={'type': 'dir'})
        self.assertTrue(b < a)

    def test_eq(self):
        a = Node('a', data={'type': 'file'})
        b = Node('b', data={'type': 'dir'})
        self.assertNotEqual(a, b)

        a = Node('a', data={'type': 'file'})
        b = Node('a', data={'type': 'file'})
        self.assertEqual(a, b)

    def test_add_path_and_find_child(self):
        # Level 1 (root)
        self.assertEqual(set(c.name for c in self.root.children), set('ah'))

        # Level 2
        node_a = self.root.find_child('a')
        node_h = self.root.find_child('h')
        self.assertEqual(set(c.name for c in node_a.children), set('bd'))
        self.assertEqual(set(c.name for c in node_h.children), set('in'))

        # Level 3
        node_b = node_a.find_child('b')
        node_i = node_h.find_child('i')
        self.assertEqual(set(c.name for c in node_b.children), set('cf'))
        self.assertEqual(set(c.name for c in node_i.children), set('k'))

        # Level 4
        node_c = node_b.find_child('c')
        node_k = node_i.find_child('k')
        self.assertEqual(set(c.name for c in node_c.children), set())
        self.assertEqual(set(c.name for c in node_k.children), set('lmp'))

        # Return None if child can't be found
        self.assertFalse(node_c.find_child('x'))

    def test_find_child_wildcard(self):
        root = Node('root')
        root.add_path('a')
        root.add_path('{b}')
        root.add_path('c')

        self.assertEqual(root.find_child('a').name, 'a')
        self.assertEqual(root.find_child('c').name, 'c')
        self.assertEqual(root.find_child('x').name, '{b}')
        self.assertFalse(root.find_child('x', wildcard=False))

    def test_ls(self):
        self.assertEqual([n.name for n in self.root.ls('a')], list('bd'))
        self.assertEqual([n.name for n in self.root.ls('a', 'b')], list('cf'))
        self.assertEqual([n.name for n in self.root.ls('a', 'b', 'c')], [])
        self.assertEqual([n.name for n in self.root.ls('h', 'i', 'k')],
                         list('lmp'))

    def test_ls_root(self):
        self.assertEqual([n.name for n in self.root.ls()], list('ah'))

    def test_ls_non_existing(self):
        self.assertEqual([n.name for n in self.root.ls('x')], [])
        self.assertEqual([n.name for n in self.root.ls('a', 'b', 'x')], [])

    def test_ls_parent(self):
        self.assertEqual([n.name for n in self.root.ls('..')], list('ah'))
        self.assertEqual([n.name for n in self.root.ls('..', '..', '..')],
                         list('ah'))
        self.assertEqual([n.name for n in self.root.ls('..', '..', 'h')],
                         list('in'))
        self.assertEqual(
            [n.name for n in self.root.ls('..', '..', 'h', '..', 'a')],
            list('bd'))

    def test_ls_dot(self):
        self.assertEqual([n.name for n in self.root.ls('.')], list('ah'))
        self.assertEqual([n.name for n in self.root.ls('.', '.', '.')],
                         list('ah'))
        self.assertEqual([n.name for n in self.root.ls('.', 'a', 'b')],
                         list('cf'))
        self.assertEqual([n.name for n in self.root.ls('.', 'h', '.')],
                         list('in'))
        self.assertEqual(
            [n.name for n in self.root.ls('.', 'h', '.', '.', 'n')], ['o'])

    def test_ls_sort_by_types(self):
        self.root.add_path('q', 'r')
        self.root.add_path('q', 's', node_type='file')
        self.root.add_path('q', 't', node_type='file')
        self.root.add_path('q', 'u')
        self.root.add_path('q', 'v', node_type='file')

        self.assertEqual([n.name for n in self.root.ls('q')],
                         list('rustv'))

    def test_add_path_with_methods(self):
        self.root.add_path('x', 'p1', node_type='file', methods={'get'})
        node_x = self.root.find_child('x')
        node_p1 = node_x.find_child('p1')
        self.assertEqual(node_p1.methods, {'get'})
        self.assertEqual(node_p1.data.get('type'), 'file')

    def test_add_path_methods_merge(self):
        self.root.add_path('x', 'p1', node_type='file', methods={'get'})
        self.root.add_path('x', 'p1', node_type='file', methods={'post'})
        node_x = self.root.find_child('x')
        node_p1 = node_x.find_child('p1')
        self.assertEqual(node_p1.methods, {'get', 'post'})

    def test_add_path_no_methods(self):
        self.root.add_path('x', 'p1', node_type='file')
        node_x = self.root.find_child('x')
        node_p1 = node_x.find_child('p1')
        self.assertEqual(node_p1.methods, set())

    def test_methods_not_set_on_dir_nodes(self):
        self.root.add_path('x', 'y', 'p1', node_type='file', methods={'get'})
        node_x = self.root.find_child('x')
        self.assertEqual(node_x.methods, set())
        node_y = node_x.find_child('y')
        self.assertEqual(node_y.methods, set())

    def test_ls_params_no_filter(self):
        self.root.add_path('q', 'r')
        self.root.add_path('q', 's', node_type='file', methods={'get'})
        self.root.add_path('q', 't', node_type='file', methods={'post'})
        self.root.add_path('q', 'u')

        result = [n.name for n in self.root.ls_params('q')]
        self.assertEqual(result, list('st'))

    def test_ls_params_with_method(self):
        self.root.add_path('q', 's', node_type='file', methods={'get'})
        self.root.add_path('q', 't', node_type='file', methods={'post'})
        self.root.add_path('q', 'u', node_type='file', methods={'get', 'post'})

        result = [n.name for n in self.root.ls_params('q', method='get')]
        self.assertEqual(result, list('su'))

        result = [n.name for n in self.root.ls_params('q', method='post')]
        self.assertEqual(result, list('tu'))

    def test_ls_params_empty_methods_passthrough(self):
        """Nodes without methods set should pass through any filter."""
        self.root.add_path('q', 's', node_type='file')
        self.root.add_path('q', 't', node_type='file', methods={'post'})

        result = [n.name for n in self.root.ls_params('q', method='get')]
        self.assertEqual(result, ['s'])

        result = [n.name for n in self.root.ls_params('q', method='post')]
        self.assertEqual(result, list('st'))

    def test_ls_params_non_existing_path(self):
        result = [n.name for n in self.root.ls_params('nonexist')]
        self.assertEqual(result, [])
