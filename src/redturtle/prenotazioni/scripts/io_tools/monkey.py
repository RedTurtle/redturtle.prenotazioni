# -*- encoding: utf-8 -*-
from bravado_core.spec import Spec
from bravado_core.spec import is_yaml
from bravado_core.spec import json
from bravado_core.spec import log
from bravado_core.spec import url2pathname
from bravado_core.spec import urlparse
from bravado_core.spec import yaml


def get_ref_handlers(self):
    return build_http_handlers(self.http_client)


def build_http_handlers(http_client):
    """Create a mapping of uri schemes to callables that take a uri. The
    callable is used by jsonschema's RefResolver to download remote $refs.

    :param http_client: http_client with a request() method

    :returns: dict like {'http': callable, 'https': callable}
    """

    def download(uri):
        log.debug("Downloading %s", uri)
        request_params = {
            "method": "GET",
            "url": uri,
        }
        response = http_client.request(request_params).result()
        content_type = response.headers.get("content-type", "").lower()
        if is_yaml(uri, content_type):
            # XXX: response.content vs. response.text
            # TODO: create PR https://github.com/Yelp/bravado-core
            try:
                return yaml.safe_load(response.content)
            except AttributeError:
                return yaml.safe_load(response.text)
        else:
            return response.json()

    def read_file(uri):
        with open(url2pathname(urlparse(uri).path), mode="rb") as fp:
            if is_yaml(uri):
                return yaml.safe_load(fp)
            else:
                return json.loads(fp.read().decode("utf-8"))

    return {
        "http": download,
        "https": download,
        # jsonschema ordinarily handles file:// requests, but it assumes that
        # all files are json formatted. We override it here so that we can
        # load yaml files when necessary.
        "file": read_file,
    }


def apply():
    Spec.get_ref_handlers = get_ref_handlers
