import pytest
from unittest import mock
from contextlib import contextmanager

from typing import Any
import argparse

from batchtools.bp import PrintJobsCommand
from tests.helpers import DictToObject


@pytest.fixture
def jobs() -> list[Any]:
    return [
        DictToObject({"model": {"metadata": {"name": "job1"}}}, name="job1"),
        DictToObject({"model": {"metadata": {"name": "job2"}}}, name="job2"),
    ]


@pytest.fixture
def pods() -> dict[str, Any]:
    return {
        "job1": [DictToObject({"model": {"metadata": {"name": "job1-pod1"}}})],
        "job2": [DictToObject({"model": {"metadata": {"name": "job2-pod1"}}})],
    }


@contextmanager
def patch_jobs_selector(
    jobs: list[DictToObject], pods: dict[str, list[Any]] | None = None
):
    def selector_side_effect(kind: str, labels: dict[str, str] | None = None):
        mock_result = mock.Mock(spec=["objects"])
        if kind == "pods" and pods is not None and labels is not None:
            job_name = labels["job-name"]
            mock_result.objects.return_value = pods[job_name]
        else:
            mock_result.objects.return_value = jobs

        return mock_result

    with mock.patch("openshift_client.selector") as mock_selector:
        mock_selector.side_effect = selector_side_effect
        yield mock_selector


def test_no_jobs(args: argparse.Namespace, capsys):
    with patch_jobs_selector([]):
        PrintJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "No jobs found" in captured.out


def test_print_jobs_all(
    args: argparse.Namespace, jobs: list[Any], pods: list[Any], capsys
):
    args.job_names = []
    with patch_jobs_selector(jobs, pods):
        PrintJobsCommand.run(args)
        captured = capsys.readouterr()
        for job in jobs:
            assert f"Pods for {job.model.metadata.name}" in captured.out
            for pod in pods[job.model.metadata.name]:
                assert pod.model.metadata.name in captured.out


def test_print_jobs_selected(
    args: argparse.Namespace, jobs: list[Any], pods: list[Any], capsys
):
    args.job_names = ["job1"]
    with patch_jobs_selector(jobs, pods):
        PrintJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "Pods for job1" in captured.out
        assert "Pods for job2" not in captured.out
        assert "job1-pod1" in captured.out
        assert "job2-pod1" not in captured.out
