import pytest
from unittest import mock
from contextlib import contextmanager

import argparse
from typing import Any
from typing import Callable

from batchtools.bl import LogsCommand
from tests.helpers import DictToObject


@pytest.fixture
def pods():
    return [
        DictToObject(
            {
                "model": {"metadata": {"name": "pod1"}},
                "logs": (
                    Callable,
                    {"return_value": {"container1": "These are logs from pod1"}},
                ),
            }
        ),
        DictToObject(
            {
                "model": {"metadata": {"name": "pod2"}},
                "logs": (
                    Callable,
                    {"return_value": {"container1": "These are logs from pod2"}},
                ),
            }
        ),
    ]


@pytest.fixture
def args() -> argparse.Namespace:
    return argparse.Namespace()


@contextmanager
def patch_pods_selector(pods: list[Any]):
    with mock.patch("openshift_client.selector") as mock_selector:
        mock_result = mock.Mock(name="result")
        mock_result.objects.return_value = pods
        mock_selector.return_value = mock_result
        yield mock_selector


def test_no_pods(args: argparse.Namespace, capsys):
    with patch_pods_selector([]):
        LogsCommand.run(args)
        captured = capsys.readouterr()
        assert "No pods to retrieve logs from" in captured.out


def test_get_logs_all(args: argparse.Namespace, pods: list[Any], capsys):
    with patch_pods_selector(pods):
        args.pod_names = []
        LogsCommand.run(args)
        captured = capsys.readouterr()
        for pod in pods:
            assert f"Logs for {pod.model.metadata.name}" in captured.out
            assert (
                f"{{'container1': 'These are logs from {pod.model.metadata.name}'}}"
                in captured.out
            )


def test_get_logs_selected(args: argparse.Namespace, pods: list[Any], capsys):
    with patch_pods_selector(pods):
        args.pod_names = ["pod1"]
        LogsCommand.run(args)
        captured = capsys.readouterr()
        assert "Logs for pod1" in captured.out
        assert "Logs for pod2" not in captured.out
