from typing import cast
from typing_extensions import override

import argparse
import sys

import openshift_client as oc

from .basecommand import Command
from .basecommand import SubParserFactory
from .helpers import oc_delete


class DeleteJobsCommandArgs(argparse.Namespace):
    job_names: list[str] | None = None


class DeleteJobsCommand(Command):
    """
    Delete specified GPU jobs, or all GPU jobs if none are specified.

    Description:
        Delete the specified jobs. If no jobs are specified, all current
        GPU-related jobs will be deleted.

    See also:
        See the repository README.md for documentation and examples.
    """

    name: str = "bd"
    help: str = "Delete specified GPU jobs, or all GPU jobs if none are specified"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "job_names", nargs="*", help="Optional list of job names to delete"
        )
        return p

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        args = cast(DeleteJobsCommandArgs, args)
        try:
            jobs = oc.selector("workloads").objects()
            if not jobs:
                print("No jobs found.")
                return

            # only get gpu jobs (ASK ABOUT THIS)
            gpu_jobs = [
                job
                for job in jobs
                # XXX: this looks wrong; jobs created by br.py do not start with job-job.
                if job.model.metadata.name.startswith("job-job")
                # XXX: this looks wrong: names cannot contain a `/`.
                or job.model.metadata.name.startswith("workloads/job-job")
            ]

            if not gpu_jobs:
                print("No GPU workloads to delete.")
                return

            # case where user provides jobs to delete
            if args.job_names:
                found = [job.model.metadata.name for job in gpu_jobs]
                for name in args.job_names:
                    if name not in found:
                        print(f"{name} is not a GPU job and cannot be deleted.")
                        continue
                    oc_delete(name)
            else:
                # case where user does not provide jobs to delete, delete all
                print("No job names provided -> deleting all GPU workloads:\n")
                for job in gpu_jobs:
                    name = job.model.metadata.name
                    oc_delete(name)

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while deleting jobs: {e}")
