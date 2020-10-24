# -*- coding: utf-8 -*-
from six.moves.urllib.parse import urlencode

import six


def urlify(url="", paths=[], params={}):
    """ We take a query string and encode it

    :param url: a string
    :param paths: a string or an iterable of path to join, e.g.:
                  - 'folder', 'folder/subfolder'
                  - ['folder', 'subfolder'], ('folder', 'subfolder')
    :param params: a dict like query string

    :return: an url
    """
    # we want path to be iterable at the end
    if isinstance(paths, six.string_types):
        paths = [paths]

    # we strip duplicate values in params
    for key in params:
        value = params[key]
        if isinstance(params[key], (list, tuple)) and len(value):
            value = value[0]
        if isinstance(value, six.text_type):
            value = value
        params[key] = value

    # we cook everything together
    if url:
        if paths:
            url = "%s/%s" % (url.rstrip("/"), "/".join(paths).lstrip("/"))
    else:
        url = "/".join(paths)
    if params:
        url = "%s?%s" % (url, urlencode(params, doseq=1))
    return url
