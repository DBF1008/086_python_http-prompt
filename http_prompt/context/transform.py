"""Functions that transform a Context object to a different representation."""

import json

from http_prompt.utils import smart_quote


def _noop(s):
    return s


def _extract_httpie_options(context, quote=False, join_key_value=False,
                            excluded_keys=None):
    if quote:
        quote_func = smart_quote
    else:
        quote_func = _noop

    if join_key_value:
        def form_new_opts(k, v): return [k + '=' + v]
    else:
        def form_new_opts(k, v): return [k, v]

    excluded_keys = excluded_keys or []

    opts = []
    for k, v in sorted(context.options.items()):
        if k not in excluded_keys:
            if v is not None:
                v = quote_func(v)
                new_opts = form_new_opts(k, v)
            else:
                new_opts = [k]
            opts += new_opts
    return opts


def _extract_httpie_request_items(context, quote=False):
    if quote:
        quote_func = smart_quote
    else:
        quote_func = _noop

    items = []
    operators_and_items = [
        # (separator, dict_of_request_items)
        ('==', context.querystring_params),
        (':=', context.body_json_params),
        ('=', context.body_params),
        (':', context.headers)
    ]
    for sep, item_dict in operators_and_items:
        for k, value in sorted(item_dict.items()):
            if sep == ':=':
                json_str = json.dumps(value,
                                      sort_keys=True)
                item = '%s:=%s' % (k, quote_func(json_str))
                items.append(item)
            elif isinstance(value, (list, tuple)):
                for v in value:
                    item = quote_func('%s%s%s' % (k, sep, v))
                    items.append(item)
            else:
                item = quote_func('%s%s%s' % (k, sep, value))
                items.append(item)
    return items


def extract_args_for_httpie_main(context, method=None):
    """Transform a Context object to a list of arguments that can be passed to
    HTTPie main function.
    """
    args = _extract_httpie_options(context)

    if method:
        args.append(method.upper())

    args.append(context.url)
    args += _extract_httpie_request_items(context)
    return args


def format_to_curl(context, method=None):
    """Format a Context object to a cURL command."""
    raise NotImplementedError('curl format is not supported yet')


def format_to_raw(context, method=None):
    """Format a Context object to HTTP raw text."""
    raise NotImplementedError('raw format is not supported yet')


def format_to_httpie(context, method=None):
    """Format a Context object to an HTTPie command."""
    cmd = ['http'] + _extract_httpie_options(context, quote=True,
                                             join_key_value=True)
    if method:
        cmd.append(method.upper())
    cmd.append(context.url)
    cmd += _extract_httpie_request_items(context, quote=True)
    return ' '.join(cmd) + '\n'


def format_to_http_prompt(context, excluded_options=None):
    """Format a Context object to HTTP Prompt commands."""
    cmds = _extract_httpie_options(context, quote=True, join_key_value=True,
                                   excluded_keys=excluded_options)
    cmds.append('cd ' + smart_quote(context.url))
    cmds += _extract_httpie_request_items(context, quote=True)
    return '\n'.join(cmds) + '\n'


def build_request_plan(context, method=None):
    """Build a structured request plan dictionary from a Context object.

    The plan mirrors what ``_call_httpie_main`` would use, so dry-run output
    and actual execution stay in sync.
    """
    return {
        'method': method.upper() if method else None,
        'url': context.url,
        'headers': dict(sorted(context.headers.items())),
        'querystring': dict(sorted(context.querystring_params.items())),
        'body_params': dict(sorted(context.body_params.items())),
        'body_json_params': dict(sorted(context.body_json_params.items())),
        'options': dict(sorted(context.options.items())),
    }


def format_request_plan(plan):
    """Format a request plan dictionary to a human-readable string."""
    lines = []

    lines.append('Method:  %s' % (plan['method'] or '(default)'))
    lines.append('URL:     %s' % plan['url'])

    if plan['headers']:
        lines.append('')
        lines.append('Headers:')
        for k, v in plan['headers'].items():
            lines.append('  %s: %s' % (k, v))

    if plan['querystring']:
        lines.append('')
        lines.append('Querystring:')
        for k, v in plan['querystring'].items():
            if isinstance(v, (list, tuple)):
                for item in v:
                    lines.append('  %s: %s' % (k, item))
            else:
                lines.append('  %s: %s' % (k, v))

    if plan['body_params']:
        lines.append('')
        lines.append('Body Parameters:')
        for k, v in plan['body_params'].items():
            lines.append('  %s: %s' % (k, v))

    if plan['body_json_params']:
        lines.append('')
        lines.append('Body JSON Parameters:')
        for k, v in plan['body_json_params'].items():
            lines.append('  %s: %s' % (k, json.dumps(v)))

    if plan['options']:
        lines.append('')
        lines.append('Options:')
        for k, v in plan['options'].items():
            if v is not None:
                lines.append('  %s: %s' % (k, v))
            else:
                lines.append('  %s' % k)

    return '\n'.join(lines) + '\n'
