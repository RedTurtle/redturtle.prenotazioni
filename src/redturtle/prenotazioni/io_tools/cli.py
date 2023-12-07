# -*- encoding: utf-8 -*-
"""Console script for io_tools."""
import importlib
import sys

import click
import yaml

from .api import Api


def load_class(klass):
    mod, klassname = klass.split(":")
    return getattr(importlib.import_module(mod), klassname)


@click.command()
@click.option("--config", default="config.yaml")
@click.option("--message", default="message.yaml")
def main(config=None, message=None, args=None):
    """Console script for io_tools."""
    CONFIG = yaml.safe_load(open(config))
    if "storage" in CONFIG:
        kwargs = CONFIG["storage"]
        klass = kwargs.pop("klass")
        storage = load_class(klass)(kwargs)
        # storage = Storage(config=CONFIG['db'])
        api = Api(secret=CONFIG["secret"], storage=storage)
    else:
        api = Api(secret=CONFIG["secret"])
    msgid = api.send_message(**yaml.safe_load(open(message)))
    if msgid:
        click.echo("sent message with msgid {}".format(msgid))
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
