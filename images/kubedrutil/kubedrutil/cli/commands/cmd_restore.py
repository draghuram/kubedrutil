
import os
import pprint
import subprocess
import sys
import time
import traceback

import click
import rfc3339

from kubedrutil.cli import context
from kubedrutil.common import kubeclient

def get_config():
    config = {}

    for name in ["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "RESTIC_PASSWORD",
                 "RESTIC_REPO", "KDR_MR_NAME", "KDR_RESTORE_DEST", "MY_POD_NAME"]:

        val = os.environ.get(name, None)
        if not val:
            raise Exception("Env variable {} is not set".format(name))

        config[name] = val

    return config

def restic_restore(config, snapID):
    restic_cmd = ["restic", "-r",  config["RESTIC_REPO"], "--verbose", "restore",  
                  "--target", config['KDR_RESTORE_DEST'], snapID]

    print("Running restic restore command: ({})".format(restic_cmd))
    resp = subprocess.run(restic_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, 
                          encoding='utf-8')
    pprint.pprint(resp)

def get_resources(config):
    resources = {}

    mr_api = kubeclient.MetadataRestoreAPI("kubedr-system")
    mbr_api = kubeclient.MetadataBackupRecordAPI("kubedr-system")

    resources["mr"] = mr_api.get(config["KDR_MR_NAME"])
    resources["mr_api"] = mr_api

    resources["mbr"] = mbr_api.get(resources["mr"]["spec"]["mbrName"])

    return resources

statusdata = {
    "restoreStatus": "Completed", 
    "restoreErrorMessage": "",
    "restoreTime": rfc3339.rfc3339(time.time(), utc=True)
}

@click.command()
@context.pass_context
def cli(ctx):
    """Perform full restore.

    """

    config = get_config()
    resources = get_resources(config)
    pod_name = config["MY_POD_NAME"]
    mr_name = config["KDR_MR_NAME"]
    mr = resources["mr"]
    mbr = resources["mbr"]

    statusdata["observedGeneration"] = mr["metadata"]["generation"]

    try:
        summary = restic_restore(config, mbr["spec"]["snapshotId"])
    except Exception as e:
        pprint.pprint(e)
        etype, value, tb = sys.exc_info()
        msg = traceback.format_exception_only(etype, value)[-1].strip()
        if isinstance(e, subprocess.CalledProcessError):
            msg += " ({})".format(e.stderr)

        statusdata["restoreStatus"] = "Failed"
        statusdata["restoreErrorMessage"] = msg

        resources["mr_api"].patch_status(mr_name, {"status": statusdata})
        kubeclient.generate_event(mr, pod_name, "RestoreFailed", msg, "Error")

        raise Exception("Restore failed") from e

    print("Setting the annotation...")
    cmd = ["kubectl", "annotate", "metadatarestore", mr_name,
           "restored.annotations.kubedr.catalogicsoftware.com=true"]
    resp = subprocess.run(cmd)

    resources["mr_api"].patch_status(mr_name, {"status": statusdata})

    kubeclient.generate_event(mr, pod_name, "RestoreSucceeded",
                              message="Restore from snapshot {} completed".format(mbr["spec"]["snapshotId"]))

