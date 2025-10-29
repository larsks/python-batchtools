from typing import cast
from typing_extensions import override

import argparse
import sys

import openshift_client as oc

from basecommand import Command
from basecommand import SubParserFactory


class PrintJobsCommandArgs(argparse.Namespace):
    job_names: list[str] | None = None


class PrintJobsCommand(Command):
    """
    Display the pod names of the specified batch jobs. If no jobs are
    specified then the pods of all current batch jobs will
    be displayed.

    See also:
        See repository README.md for more documentation and examples.
    """

    name: str = "bp"
    help: str = "Display the pod names of the specified batch jobs"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "job_names", nargs="*", help="Optional list of job names to display"
        )
        return p

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        args = cast(PrintJobsCommandArgs, args)
        try:
            jobs = oc.selector("jobs").objects()
            if not jobs:
                print("No jobs found.")
                return

            job_dict = {job.model.metadata.name: job for job in jobs}

            if args.job_names:
                for name in args.job_names:
                    if name not in job_dict:
                        print(f"{name} does not exist; cannot fetch pod name.")
                        continue
                    print_pods_for(name)
            else:
                print("Displaying pods for all current batch jobs:\n")
                for name in job_dict.keys():
                    print_pods_for(name)

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while retrieving pods: {e}")


def print_pods_for(job_name: str):
    pods = oc.selector("pods", labels={"job-name": job_name}).objects()
    if not pods:
        print(f"No pods found for job {job_name}.")
        return
    print(f"\nPods for {job_name}:\n{'-' * 40}")
    for pod in pods:
        print(f"- {pod.model.metadata.name}")
