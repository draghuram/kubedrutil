
import click

class Context(object):
    def __init__(self):
        pass

pass_context = click.make_pass_decorator(Context, ensure=True)

