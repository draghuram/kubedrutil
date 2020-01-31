
import os
import pprint
import subprocess
import time

import click
import rfc3339

from kubedrutil.cli import context
from kubedrutil.common import kubeclient

def validate_env(envlist):
    for name in envlist:
        val = os.environ.get(name, None)
        if not val:
            raise Exception("Env variable {} is not set".format(name))

def format_event_name(involvedObj):
    return "{}-{}-{}-{}".format(involvedObj["apiVersion"].replace("/", "-"), involvedObj["kind"],
                                involvedObj["metadata"]["name"],
                                involvedObj["metadata"]["resourceVersion"])

def generate_event(involvedObj, source_name, reason, message, evtype="Normal"):
    timestamp = rfc3339.rfc3339(time.time(), utc=True)

    body = {
        "kind": "Event",
        "apiVersion": "v1",
        "count": 1,
        "firstTimestamp": timestamp,
        "lastTimestamp": timestamp,
        "involvedObject": {
            "apiVersion": involvedObj["apiVersion"],
            "kind": involvedObj["kind"],
            "name": involvedObj["metadata"]["name"],
            "namespace": involvedObj["metadata"]["namespace"],
            "resourceVersion": involvedObj["metadata"]["resourceVersion"],
            "uid": involvedObj["metadata"]["uid"]
        },
        "message": message,
        "metadata": {
            "name": format_event_name(involvedObj),
            "namespace": involvedObj["metadata"]["namespace"]
        },
        "reason": reason,
        "source": {
            "component": source_name
        },
        "type": evtype
    }

    event_api = kubeclient.EventAPI("kubedr-system")
    event_api.create(body)

@click.command()
@context.pass_context
def cli(ctx):
    """Initialize a backup repository.

    """

    validate_env(["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "RESTIC_PASSWORD", 
                  "RESTIC_REPO", "KDR_BACKUPLOC_NAME", ])
    name = os.environ["KDR_BACKUPLOC_NAME"]
    backuploc_api = kubeclient.BackupLocationAPI("kubedr-system")
    backup_loc = backuploc_api.get(name)
    pod_name = os.environ["MY_POD_NAME"]

    statusdata = {
        "initStatus": "Completed", 
        "initErrorMessage": "",
        "initTime": time.asctime()
    }

    cmd = ["restic", "-r", os.environ["RESTIC_REPO"], "--verbose", "init"]
    print("Running the init command: ({})".format(cmd))
    resp = subprocess.run(cmd, stderr=subprocess.PIPE)
    pprint.pprint(resp)

    if resp.returncode != 0:
        # Initialization failed.
        errMsg = resp.stderr.decode("utf-8")
        statusdata["initStatus"] = "Failed"
        statusdata["initErrorMessage"] = errMsg
        backuploc_api.patch_status(name, {"status": statusdata})
        generate_event(backup_loc, pod_name, "InitFailed", errMsg, "Error")

        raise Exception("Initialization failed, reason: {}".format(errMsg))

    print("Setting the annotation...")
    cmd = ["kubectl", "annotate", "backuplocation", name,
           "initialized.annotations.kubedr.catalogicsoftware.com=true"]
    resp = subprocess.run(cmd)
    backuploc_api.patch_status(name, {"status": statusdata})

    generate_event(backup_loc, pod_name, "InitSucceeded",
                   message="Repo at {} is successfully initialized".format(os.environ["RESTIC_REPO"]))



