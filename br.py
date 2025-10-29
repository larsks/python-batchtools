from typing import cast
import typing_extensions
from typing_extensions import override

import argparse
import os
import socket
import sys
import time

import openshift_client as oc

from basecommand import Command
from basecommand import SubParserFactory
from build_yaml import build_job_body
from helpers import pretty_print
from helpers import oc_delete
from file_setup import prepare_context


class CreateJobCommandArgs(argparse.Namespace):
    gpu: str = "v100"
    image: str = "image-registry.openshift-image-registry.svc:5000/redhat-ods-applications/csw-run-f25:latest"
    context: bool = True
    name: str = "job"
    job_id: int = os.getpid()
    job_delete: bool = True
    wait: bool = True
    timeout: int = 60 * 15 * 4
    max_sec: int = 60 * 15
    gpu_numreq: int = 1
    gpu_numlim: int = 1
    verbose: int = 0
    command: list[str] = []


class CreateJobCommand(Command):
    """
    brun creates and submits a batch job to a GPU batch queue using the OpenShift Python client.
    The arguments are treated as a command line that will execute as the batch job within a container.
    The behaviour of the job submission can be controlled via several environment variables or CLI flags.

    By default, the job runs in an isolated container environment scheduled onto a GPU node using
    the Kueue queue system. GPU type, image, resource limits, and runtime behavior (e.g., waiting or
    automatic deletion) can be customized at submission time.

    Example usages:

    1. Run a simple command on the default GPU type (v100)
    $ brun ./hello
    Hello from CPU
    Hello from GPU
    ...
    RUNDIR: jobs/job-v100-9215

    2. Specify GPU type and image for a training job
    $ br --gpu a100 --image quay.io/user/train:latest cuda-code

    3. Submit without waiting for completion
    $ br --wait 0 ./long_running_task.sh

    By default, br waits for the job to complete, streams its logs,
    and then displays the directory where the job outputs were copied.

    See also:
        See the repository README.md for more examples and advanced usage.
    """

    name: str = "br"
    help: str = "Create and submit a GPU batch job"

    @classmethod
    @override
    def build_parser(cls, subparsers: SubParserFactory):
        p = super().build_parser(subparsers)
        p.add_argument(
            "--gpu",
            default=CreateJobCommandArgs.gpu,
            help=f"Select GPU type (default {CreateJobCommandArgs.gpu})",
        )
        p.add_argument(
            "--image",
            default=CreateJobCommandArgs.image,
            help=f"Specify container image for job (default {CreateJobCommandArgs.image})",
        )
        p.add_argument(
            "--context",
            action=argparse.BooleanOptionalAction,
            default=CreateJobCommandArgs.context,
            help=f"Copy working directory (default {CreateJobCommandArgs.context})",
        )
        p.add_argument(
            "--name",
            default=CreateJobCommandArgs.name,
            help=f"Base job name (default {CreateJobCommandArgs.name})",
        )
        p.add_argument(
            "--job-id",
            default=CreateJobCommandArgs.job_id,
            type=int,
            help="Job ID suffix (default current pid)",
        )
        p.add_argument(
            "--job-delete",
            action=argparse.BooleanOptionalAction,
            default=CreateJobCommandArgs.job_delete,
            help=f"Delete job on completion (default {CreateJobCommandArgs.job_delete})",
        )
        p.add_argument(
            "--wait",
            action=argparse.BooleanOptionalAction,
            default=CreateJobCommandArgs.wait,
            help=f"Wait for job completion (default {CreateJobCommandArgs.wait})",
        )
        p.add_argument(
            "--timeout",
            default=CreateJobCommandArgs.timeout,
            type=int,
            help=f"Wait timeout in seconds (default {CreateJobCommandArgs.timeout})",
        )
        p.add_argument(
            "--max-sec",
            default=CreateJobCommandArgs.max_sec,
            type=int,
            help=f"Maximum execution time in seconds (default {CreateJobCommandArgs.max_sec})",
        )
        p.add_argument(
            "--gpu-numreq",
            default=CreateJobCommandArgs.gpu_numreq,
            type=int,
            help=f"Number of GPUs requested (default {CreateJobCommandArgs.gpu_numreq})",
        )
        p.add_argument(
            "--gpu-numlim",
            default=CreateJobCommandArgs.gpu_numlim,
            type=int,
            help=f"Number of GPUs limited (default {CreateJobCommandArgs.gpu_numlim})",
        )
        p.add_argument(
            "command",
            nargs=argparse.REMAINDER,
            help="Command to run inside the container",
        )

        return p

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        args = cast(CreateJobCommandArgs, args)
        DEFAULT_QUEUES = {
            "v100": "v100-localqueue",
            "a100": "a100-localqueue",
            "h100": "h100-localqueue",
            "none": "dummy-localqueue",
        }

        if args.gpu not in DEFAULT_QUEUES:
            sys.exit(f"ERROR: unsupported GPU {args.gpu} : no queue found")
        queue_name = DEFAULT_QUEUES[args.gpu]

        job_name = f"{args.name}-{args.gpu}-{args.job_id}"
        container_name = f"{job_name}-container"
        file_to_execute = " ".join(args.command).strip()

        pwd = os.getcwd()
        context_directory = pwd
        jobs_directory = os.path.join(pwd, "jobs")

        output_directory = os.path.join(jobs_directory, job_name)
        dev_pod_name = socket.gethostname()
        getlist = os.path.join(output_directory, "getlist")

        pod = oc.selector(f"pod/{dev_pod_name}").object()
        container = getattr(pod.model.spec, "containers", []) or []
        dev_container_name = container[0].name

        prepare_context(
            context=args.context,
            context_dir=context_directory,
            jobs_dir=jobs_directory,
            output_dir=output_directory,
            getlist_path=getlist,
        )

        try:
            # Create job body using the helper
            job_body = build_job_body(
                job_name=job_name,
                queue_name=queue_name,
                image=args.image,
                container_name=container_name,
                cmdline=file_to_execute,
                max_sec=args.max_sec,
                gpu=args.gpu,
                gpu_req=args.gpu_numreq,
                gpu_lim=args.gpu_numlim,
                context=args.context,
                devpod_name=dev_pod_name,
                devcontainer=dev_container_name,
                context_dir=context_directory,
                jobs_dir=jobs_directory,
                getlist_path=getlist,
            )

            print(f"Creating job {job_name} in {queue_name}...")
            oc.create(job_body)
            print(f"Job: {job_name} created successfully. Now checking pod...")
            if args.wait:
                log_job_output(job_name=job_name, wait=True, timeout=args.timeout)

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while creating job: {e}")

        if args.job_delete and args.wait:
            print(f"RUNDIR: jobs/{job_name}")
            oc_delete(job_name)
        else:
            print(
                f"User specified not to wait, or not to delete, so {job_name} must be deleted by user."
            )
            print("You can do this by running:")
            print(f"bd {job_name} OR ")
            print(f"oc delete job {job_name}")


def get_pod_status(pod_name: str | None = None) -> str:
    """
    Return the current status.phase of a pod (Pending, Running, Succeeded, Failed).
    """
    pod = oc.selector(f"pod/{pod_name}").object()
    return pod.model.status.phase or "Unknown"


def log_job_output(job_name: str, *, wait: bool, timeout: int | None) -> None:
    """
    Wait until the job's pod completes (Succeeded/Failed), then print its logs once.
    """
    pods = oc.selector("pod", labels={"job-name": job_name}).objects()
    if not pods:
        print(f"No pods found for job {job_name}")
        return

    pod = pods[0]
    pod_name = pod.model.metadata.name

    if wait:
        start = time.monotonic()
        while True:
            phase = get_pod_status(pod_name)
            if phase in ("Succeeded", "Failed"):
                print(f"Pod, {pod_name} finished with phase={phase}")
                break
            if timeout and (time.monotonic() - start) > timeout:
                print(f"Timeout waiting for pod {pod_name} to complete")
                print(f"Deleting pod {pod_name}")
                oc_delete(job_name)
                return

            # sleep to avoid hammering the server
            time.sleep(2)
    # pass in the pod object to get logs from, not the name
    print(pretty_print(pod))
