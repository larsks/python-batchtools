from typing_extensions import override
from typing import cast

import sys
import argparse
import openshift_client as oc

from .basecommand import Command
from .basecommand import SubParserFactory
from .helpers import pretty_print


class LogsCommandArgs(argparse.Namespace):
    pod_names: list[str] | None = None


class LogsCommand(Command):
    """
    Display logs of specified pods. If none are specified then logs for all
    pods of all current batch jobs will be display.

    See also:
        See repository README.md for more documentation and examples.
    """

    name: str = "bl"
    help: str = "Display logs of specific pods"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "pod_names",
            nargs="*",
            help="Optional list of pod names for which to display logs",
        )
        return p

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        args = cast(LogsCommandArgs, args)
        try:
            pods = oc.selector("pods").objects()

            if not pods:
                print("No pods to retrieve logs from.")
                return

            # dict of pod name and pod object
            pod_dict: dict[str, oc.APIObject] = {
                pod.model.metadata.name: pod for pod in pods
            }

            # case where user provides pods
            if args.pod_names:
                for name in args.pod_names:
                    if name not in pod_dict:
                        print(f"{name} is not a valid pod. Logs cannot be retrieved.")
                        continue
                    print(f"\nLogs for {name}:\n{'-' * 40}")
                    print(pretty_print(pod_dict[name]))

            else:
                # case where user provides no args, print logs for all pods
                for name, pod in pod_dict.items():
                    print(f"\nLogs for {name}:\n{'-' * 40}")
                    print(pretty_print(pod))

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while retrieving logs: {e}")
