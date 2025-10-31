from openshift_client import OpenShiftPythonException
import pytest
from unittest import mock
from contextlib import contextmanager

import argparse

from batchtools.bd import DeleteJobsCommand
from tests.helpers import DictToObject


@pytest.fixture
def jobs():
    return [
        DictToObject(
            {
                "model": {"metadata": {"name": "job-job-1"}},
            }
        ),
        DictToObject(
            {
                "model": {"metadata": {"name": "job-job-2"}},
            }
        ),
    ]


@pytest.fixture
def ignored_jobs():
    return [
        DictToObject(
            {
                "model": {"metadata": {"name": "ignored-1"}},
            }
        ),
    ]


@pytest.fixture
def failed_jobs():
    return [
        DictToObject(
            {
                "model": {"metadata": {"name": "job-job-1"}},
            }
        ),
    ]


@contextmanager
def patch_jobs_selector(jobs: list[DictToObject]):
    with mock.patch("openshift_client.selector") as mock_selector:
        mock_result = mock.Mock(name="result")
        mock_result.objects.return_value = jobs
        mock_selector.return_value = mock_result
        yield mock_selector


def test_no_jobs(args: argparse.Namespace, capsys):
    with patch_jobs_selector([]):
        DeleteJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "No jobs found" in captured.out


def test_no_gpu_jobs(args: argparse.Namespace, ignored_jobs, capsys):
    with patch_jobs_selector(ignored_jobs):
        DeleteJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "No GPU workloads to delete" in captured.out


def test_delete_jobs(args: argparse.Namespace, jobs, capsys):
    args.job_names = []
    with (
        patch_jobs_selector(jobs),
        mock.patch("openshift_client.invoke") as mock_invoke,
    ):
        DeleteJobsCommand.run(args)
        captured = capsys.readouterr()
        for job, ca in zip(jobs, mock_invoke.call_args_list):
            assert f"Deleting {job.model.metadata.name}" in captured.out
            assert ca.args == ("delete", ["job", job.model.metadata.name])


def test_delete_jobs_fail(args: argparse.Namespace, failed_jobs, capsys):
    args.job_names = []
    with (
        patch_jobs_selector(failed_jobs),
        mock.patch("openshift_client.invoke") as mock_invoke,
    ):
        mock_invoke.side_effect = OpenShiftPythonException("test exception")
        DeleteJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "Error occurred while deleting job: test exception" in captured.out
