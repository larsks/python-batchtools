from unittest import mock
from contextlib import contextmanager

import argparse

from bj import ListJobsCommand
from tests.helpers import DictToObject


@contextmanager
def patch_jobs_selector(jobs: list[DictToObject]):
    with mock.patch("openshift_client.selector") as mock_selector:
        mock_result = mock.Mock(name="result")
        mock_result.objects.return_value = jobs
        mock_selector.return_value = mock_result
        yield mock_selector


def test_no_jobs(args: argparse.Namespace, capsys):
    with patch_jobs_selector([]):
        ListJobsCommand.run(args)
        captured = capsys.readouterr()
        assert "No jobs found" in captured.out


def test_list_jobs(args: argparse.Namespace, capsys):
    jobs = [
        DictToObject({"model": {"metadata": {"name": "job1"}}}),
        DictToObject({"model": {"metadata": {"name": "job2"}}}),
    ]
    with patch_jobs_selector(jobs):
        ListJobsCommand.run(args)
        captured = capsys.readouterr()
        assert f"Found {len(jobs)} jobs" in captured.out
        for job in jobs:
            assert job.model.metadata.name in captured.out
