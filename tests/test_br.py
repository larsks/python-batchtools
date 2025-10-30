import pytest
from unittest import mock

import tempfile
import argparse

from br import CreateJobCommand
from tests.helpers import DictToObject


@pytest.fixture
def tempdir():
    with tempfile.TemporaryDirectory() as t:
        yield t


def test_invalid_gpu(args: argparse.Namespace):
    args.gpu = "invalid"
    args.command = ["true"]
    with pytest.raises(SystemExit) as err:
        CreateJobCommand.run(args)

    assert "ERROR: unsupported GPU invalid" in err.value.code


@mock.patch("openshift_client.create", name="create")
@mock.patch("openshift_client.selector", name="selector")
@mock.patch("socket.gethostname", name="gethostname")
@mock.patch("os.getcwd", name="getcwd")
def test_create_job_nowait(
    mock_getcwd,
    mock_gethostname,
    mock_selector,
    mock_create,
    args: argparse.Namespace,
    tempdir,
    parser,
    subparsers,
):
    CreateJobCommand.build_parser(subparsers)
    args = parser.parse_args(["br"])
    args.wait = False
    args.job_id = 123
    args.command = ["true"]

    mock_getcwd.return_value = tempdir
    mock_gethostname.return_value = "testhost"

    pod = DictToObject(
        {
            "model": {
                "metadata": {"name": "testpod"},
                "spec": {"containers": [{"name": "container1"}]},
            }
        }
    )

    mock_result = mock.Mock(spec=["object"])
    mock_result.object.return_value = pod
    mock_selector.return_value = mock_result

    expected = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": "job-v100-123",
            "labels": {
                "kueue.x-k8s.io/queue-name": "v100-localqueue",
                "test_name": "kueue_test",
            },
        },
        "spec": {
            "parallelism": 1,
            "completions": 1,
            "backoffLimit": 0,
            "activeDeadlineSeconds": 900,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "job-v100-123-container",
                            "image": "image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/csw-run-f25:latest",
                            "command": [
                                "/bin/bash",
                                "-c",
                                f"\nset -e\nexport RSYNC_RSH='oc rsh -c container1'\n\nmkdir -p job-v100-123\n\nrsync -q --archive --no-owner --no-group --omit-dir-times     --numeric-ids testhost:{tempdir}/jobs/job-v100-123/getlist job-v100-123/getlist\nrsync -q -r --archive --no-owner --no-group     --omit-dir-times --numeric-ids --files-from=job-v100-123/getlist     testhost:{tempdir}/ job-v100-123/\nfind job-v100-123 -mindepth 1 -maxdepth 1 > job-v100-123/gotlist\n\n(\n  cd job-v100-123 &&  |& tee job-v100-123.log\n)\n\nrsync -q --archive --no-owner --no-group     --omit-dir-times --no-relative --numeric-ids      --exclude-from=job-v100-123/gotlist     job-v100-123 testhost:{tempdir}/jobs\n",
                        ],
                            "resources": {
                                "requests": {"nvidia.com/gpu": "1"},
                                "limits": {"nvidia.com/gpu": "1"},
                            },
                        }
                    ],
                }
            },
        },
    }

    CreateJobCommand.run(args)

    assert mock_create.call_args.args[0] == expected
