
import os
import subprocess

import click

from kubedrutil.cli import context

def validate_env(envlist):
    for name in envlist:
        val = os.environ.get(name, None)
        if not val:
            raise Exception("Env variable {} is not set".format(name))

@click.command()
@context.pass_context
def cli(ctx):
    """Initialize a backup repository.

    """

    validate_env(["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "RESTIC_PASSWORD", 
                  "RESTIC_REPO", "KDR_BACKUPLOC_NAME", ])

    cmd = ["restic", "-r", os.environ["RESTIC_REPO"], "--verbose", "init"]
    print("Running the init command: ({})".format(cmd))
    resp = subprocess.run(cmd)
    print(resp)

    if resp.returncode == 0:
        print("Setting the annotation...")
        cmd = ["kubectl", "annotate", "backuplocation", os.environ["KDR_BACKUPLOC_NAME"],
               "initialized.annotations.kubedr.catalogicsoftware.com=true"]
        resp = subprocess.run(cmd)
        print(resp)


