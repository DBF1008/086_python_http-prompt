from http_prompt.context import Context


def test_creation():
    context = Context('http://example.com')
    assert context.url == 'http://example.com'
    assert context.options == {}
    assert context.headers == {}
    assert context.querystring_params == {}
    assert context.body_params == {}
    assert not context.should_exit


def test_creation_with_longer_url():
    context = Context('http://example.com/a/b/c/index.html')
    assert context.url == 'http://example.com/a/b/c/index.html'
    assert context.options == {}
    assert context.headers == {}
    assert context.querystring_params == {}
    assert context.body_params == {}
    assert not context.should_exit


def test_eq():
    c1 = Context('http://localhost')
    c2 = Context('http://localhost')
    assert c1 == c2

    c1.options['--verify'] = 'no'
    assert c1 != c2


def test_copy():
    c1 = Context('http://localhost')
    c2 = c1.copy()
    assert c1 == c2
    assert c1 is not c2


def test_update():
    c1 = Context('http://localhost')
    c1.headers['Accept'] = 'application/json'
    c1.querystring_params['flag'] = '1'
    c1.body_params.update({
        'name': 'John Doe',
        'email': 'john@example.com'
    })

    c2 = Context('http://example.com')
    c2.headers['Content-Type'] = 'text/html'
    c2.body_params['name'] = 'John Smith'

    c1.update(c2)

    assert c1.url == 'http://example.com'
    assert c1.headers == {
        'Accept': 'application/json',
        'Content-Type': 'text/html'
    }
    assert c1.querystring_params == {'flag': '1'}
    assert c1.body_params == {
        'name': 'John Smith',
        'email': 'john@example.com'
    }


def test_update_type_switch_form_to_json():
    c1 = Context('http://localhost')
    c1.body_params['name'] = 'alice'

    c2 = Context(None)
    c2.body_json_params['name'] = 'bob'

    c1.update(c2)
    assert 'name' not in c1.body_params
    assert c1.body_json_params == {'name': 'bob'}


def test_update_type_switch_json_to_form():
    c1 = Context('http://localhost')
    c1.body_json_params['count'] = 5

    c2 = Context(None)
    c2.body_params['count'] = 'five'

    c1.update(c2)
    assert 'count' not in c1.body_json_params
    assert c1.body_params == {'count': 'five'}


def test_update_preserves_unrelated_keys():
    c1 = Context('http://localhost')
    c1.body_params['name'] = 'alice'
    c1.body_json_params['age'] = 30

    c2 = Context(None)
    c2.body_json_params['name'] = 'bob'

    c1.update(c2)
    assert c1.body_params == {}
    assert c1.body_json_params == {'age': 30, 'name': 'bob'}


def test_spec():
    c = Context('http://localhost', spec={
        'paths': {
            '/users': {
                'get': {
                    'parameters': [
                        {'name': 'username', 'in': 'path'},
                        {'name': 'since', 'in': 'query'},
                        {'name': 'Accept'}
                    ]
                }
            },
            '/orgs/{org}': {
                'get': {
                    'parameters': [
                        {'name': 'org', 'in': 'path'},
                        {'name': 'featured', 'in': 'query'},
                        {'name': 'X-Foo', 'in': 'header'}
                    ]
                }
            }
        }
    })
    assert c.url == 'http://localhost'

    root_children = list(sorted(c.root.children))
    assert len(root_children) == 2
    assert root_children[0].name == 'orgs'
    assert root_children[1].name == 'users'

    orgs_children = list(sorted(root_children[0].children))
    assert len(orgs_children) == 1

    org_children = list(sorted(list(orgs_children)[0].children))
    assert len(org_children) == 2
    assert org_children[0].name == 'X-Foo'
    assert org_children[1].name == 'featured'

    users_children = list(sorted(root_children[1].children))
    assert len(users_children) == 2
    assert users_children[0].name == 'Accept'
    assert users_children[1].name == 'since'


def test_override():
    """Parameters can be defined at path level
    """
    c = Context('http://localhost', spec={
        'paths': {
            '/users': {
                'parameters': [
                    {'name': 'username', 'in': 'query'},
                    {'name': 'Accept', 'in': 'header'}
                ],
                'get': {
                    'parameters': [
                        {'name': 'custom1', 'in': 'query'}
                    ]
                },
                'post': {
                    'parameters': [
                        {'name': 'custom2', 'in': 'query'},
                    ]
                },
            },
            '/orgs': {
                'parameters': [
                    {'name': 'username', 'in': 'query'},
                    {'name': 'Accept', 'in': 'header'}
                ],
                'get': {}
            }
        }
    })
    assert c.url == 'http://localhost'

    root_children = list(sorted(c.root.children))
    # one path
    assert len(root_children) == 2
    assert root_children[0].name == 'orgs'
    assert root_children[1].name == 'users'

    orgs_methods = list(sorted(list(root_children)[0].children))
    # path parameters are used even if no method parameter
    assert len(orgs_methods) == 2
    assert next(filter(lambda i:i.name == 'username', orgs_methods), None) is not None
    assert next(filter(lambda i:i.name == 'Accept', orgs_methods), None) is not None

    users_methods = list(sorted(list(root_children)[1].children))
    # path and methods parameters are merged
    assert len(users_methods) == 4
    assert next(filter(lambda i:i.name == 'username', users_methods), None) is not None
    assert next(filter(lambda i:i.name == 'custom1', users_methods), None) is not None
    assert next(filter(lambda i:i.name == 'custom2', users_methods), None) is not None
    assert next(filter(lambda i:i.name == 'Accept', users_methods), None) is not None
