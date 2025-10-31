import pytest
from unittest import mock

import tempfile
import argparse

import build_yaml
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


@pytest.mark.parametrize(
    "gpu, resources",
    [
        (
            "v100",
            {
                "requests": {"nvidia.com/gpu": "1"},
                "limits": {"nvidia.com/gpu": "1"},
            },
        ),
        (
            "none",
            {
                "requests": {"cpu": "1", "memory": "1Gi"},
                "limits": {"cpu": "1", "memory": "1Gi"},
            },
        ),
    ],
)
@mock.patch("openshift_client.create", name="create")
@mock.patch("openshift_client.selector", name="selector")
@mock.patch("socket.gethostname", name="gethostname")
@mock.patch("os.getcwd", name="getcwd")
def test_create_job_nowait(
    mock_getcwd,
    mock_gethostname,
    mock_selector,
    mock_create,
    gpu,
    resources,
    args: argparse.Namespace,
    tempdir,
    parser,
    subparsers,
):
    CreateJobCommand.build_parser(subparsers)
    args = parser.parse_args(["br"])
    args.wait = False
    args.job_id = "test"
    args.image = "test-image"
    args.gpu = gpu
    args.command = ["true"]

    queue_name = "dummy-localqueue" if gpu == "none" else f"{gpu}-localqueue"

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
            "name": f"job-{gpu}-test",
            "labels": {
                "kueue.x-k8s.io/queue-name": queue_name,
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
                            "command": [
                                "/bin/bash",
                                "-c",
                                f"testcommand {' '.join(args.command).strip()}",
                            ],
                            "name": f"job-{gpu}-test-container",
                            "image": "test-image",
                            "resources": resources,
                        }
                    ],
                }
            },
        },
    }

    build_yaml.rsync_script = "testcommand {cmdline}"
    CreateJobCommand.run(args)

    assert mock_create.call_args.args[0] == expected
