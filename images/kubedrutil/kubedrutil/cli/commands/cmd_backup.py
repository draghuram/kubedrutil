
import os
import json
import pprint
import subprocess
import sys
import time
import traceback

import click

from kubedrutil.cli import context
from kubedrutil.common import kubeclient

def get_config():
    config = {}

    for name in ["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "RESTIC_PASSWORD",
                 "ETCD_ENDPOINT", "ETCD_CREDS_DIR", "ETCD_SNAP_PATH",
                 "RESTIC_REPO", "BACKUP_SRC", "KDR_POLICY_NAME"]:

        val = os.environ.get(name, None)
        if not val:
            raise Exception("Env variable {} is not set".format(name))

        config[name] = val

    return config

def build_snapshot_cmd(config):
    cmd = [
        "etcdctl",
        "--endpoints={}".format(config["ETCD_ENDPOINT"]),
        "--cacert={}/ca.crt".format(config["ETCD_CREDS_DIR"]),
        "--cert={}/client.crt".format(config["ETCD_CREDS_DIR"]),
        "--key={}/client.key".format(config["ETCD_CREDS_DIR"]),
	"--debug", "snapshot", "save",
        config["ETCD_SNAP_PATH"]
    ]

    return cmd

def create_etcd_snapshot(config):
    snapshot_cmd = build_snapshot_cmd(config)
    print("Running the etcd snapshot command: ({})".format(snapshot_cmd))
    os.environ["ETCDCTL_API"] = "3"

    # etcdctl is writing debug information to STDERR so don't capture it.
    resp = subprocess.run(snapshot_cmd, check=True, encoding='utf-8')

    # The command doesn't return non-zero error code even when it fails
    # (at least in some cases) so explicitly check for the snapshot file.
    fileinfo = os.stat(config["ETCD_SNAP_PATH"])
    if fileinfo.st_size <= 0:
        raise Exception("etcd snapshot file {} has invalid size".format(config["ETCD_SNAP_PATH"]))

    pprint.pprint(resp)

def copy_certificates(config):
    src_dir = config.get('CERTS_SRC_DIR', None)
    dest_dir = config.get('CERTS_DEST_DIR', None)

    if src_dir and dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
        copy_cmd = ["cp", "-R",  '"{}"/*'.format(src_dir), '"{}"'.format(dest_dir)]
        resp = subprocess.run(copy_cmd, stderr=subprocess.PIPE, check=True, encoding='utf-8', shell=True)
        pprint.pprint(resp)

def restic_backup(config):
    restic_cmd = ["restic", "--json",  "-r",  config['RESTIC_REPO'],
                  "--verbose", "backup",  config['BACKUP_SRC']]
    print("Running restic backup command: ({})".format(restic_cmd))
    resp = subprocess.run(restic_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, 
                          encoding='utf-8')
    pprint.pprint("    rc = {}".format(resp.returncode))

    snapshot_id = None
    print()
    for line in resp.stdout.splitlines():
        print(line)
        line = line.strip()

        if not line:
            continue

        try:
            data = json.loads(line)
        except json.decoder.JSONDecodeError:
            # restic may output some lines in plain text so ignore decode errors.
            print("    Ignoring decode error")
            continue
        else:
            if data["message_type"].lower() == "summary":
                return data

    raise Exception("Could not find summary in restic output")

def create_mbr(policy, snapshot_id):
    mbr_name = "mbr-{}".format(snapshot_id)
    print("mbr_name: {}".format(mbr_name))
    mbr_api = kubeclient.MetadataBackupRecordAPI("kubedr-system")
    mbr_spec = {
        "snapshotId": snapshot_id,
        "policy": policy
    }
    pprint.pprint(mbr_spec)
    print("Creating MBR...")
    mbr_api.create(mbr_name, mbr_spec)

def backup(config):
    create_etcd_snapshot(config)
    copy_certificates(config)

    summary = restic_backup(config)
    create_mbr(config["KDR_POLICY_NAME"], summary["snapshot_id"])

    return summary

@click.command()
@context.pass_context
def cli(ctx):
    """Perform backup of etcd and optionally, certificates as well.

    """

    statusdata = {
        "backupStatus": "Completed", 
        "backupErrorMessage": "",
        "backupTime": time.asctime()
    }
    mbp_api = kubeclient.MetadataBackupPolicyAPI("kubedr-system")
    config = get_config()
    policy_name = config["KDR_POLICY_NAME"]
    policy = mbp_api.get(policy_name)
    pod_name = os.environ["MY_POD_NAME"]

    try:
        summary = backup(config)
    except Exception as e:
        statusdata["backupStatus"] = "Failed"
        etype, value, tb = sys.exc_info()
        msg = traceback.format_exception_only(etype, value)[-1].strip()
        if isinstance(e, subprocess.CalledProcessError):
            msg += " ({})".format(e.stderr)

        statusdata["backupErrorMessage"] = msg
        mbp_api.patch_status(policy_name, {"status": statusdata})
        kubeclient.generate_event(policy, pod_name, "BackupFailed", msg, "Error")
        raise Exception("Backup failed") from e

    statusdata["filesNew"] = summary["files_new"]
    statusdata["filesChanged"] = summary["files_changed"]
    statusdata["dataAdded"] = summary["data_added"]
    statusdata["totalBytesProcessed"] = summary["total_bytes_processed"]
    statusdata["totalDurationSecs"] = str(summary["total_duration"])
    statusdata["snapshotId"] = summary["snapshot_id"]

    mbp_api.patch_status(policy_name, {"status": statusdata})
    kubeclient.generate_event(policy, pod_name, "BackupSucceeded",
                              message="Backup completed, snapshot ID: {}".format(summary["snapshot_id"]))


