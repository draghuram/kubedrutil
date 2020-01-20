#!/usr/bin/env python
#-*- mode: Python;-*-

import atexit
import json
import logging
import os
import sys
import tempfile
import traceback

import click

from kubedrutil.cli import context

cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))

class MyCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')

            mod = __import__('kubedrutil.cli.commands.cmd_' + name, None, None, ['cli'])
        except ImportError:
            logging.error(traceback.format_exc())
            return

        return mod.cli

@click.command(cls=MyCLI)
@click.version_option('0.1.2')
@context.pass_context
def cli(ctx):
    """Kubedrutil CLI.
    """

    pass

def init_logging():
    fd, logfile = tempfile.mkstemp(suffix='.txt', prefix='kubedrutil')
    os.close(fd)
    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)-15s: %(levelname)s: %(message)s')

    # Use "CRITICAL" for logging messages that should go to console as well as to the
    # log file. If we use "INFO" level, stack traces will end up on console (because they
    # will be logged at "ERROR" level.
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL)
    ch.setFormatter(logging.Formatter(''))
    logger.addHandler(ch)

    return logfile

def main():
    logfile = init_logging()
    # logging.critical("logfile: {}".format(logfile))

    try:
        cli()
    except Exception as e:
        logging.error(traceback.format_exc())

        exctype, value = sys.exc_info()[:2]
        click.secho(traceback.format_exception_only(exctype, value)[0], fg='red')

        sys.exit(1)
