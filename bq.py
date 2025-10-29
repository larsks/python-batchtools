from typing_extensions import override

import argparse
import sys

import openshift_client as oc

from basecommand import Command


class GpuQueuesCommand(Command):
    """
    Display the status of the GPU queues for the cluster.

    This command shows the number of admitted (active), pending, and reserved jobs
    on each queue. It also displays how many GPUs service each queue and the
    queuing strategy being used.

    See also:
        See the repository README.md for more documentation and examples.
    """

    name: str = "bq"
    help: str = "Display the status of the GPU queues for the cluster"

    @staticmethod
    @override
    def run(args: argparse.Namespace):
        try:
            clusterqueues = oc.selector("clusterqueue").objects()
            if not clusterqueues:
                print("No ClusterQueues found.")

            for cq in clusterqueues:
                cq_dict = cq.as_dict() if hasattr(cq, "as_dict") else cq.model.to_dict()
                meta = cq_dict.get("metadata", {})
                spec = cq_dict.get("spec", {})
                status = cq_dict.get("status", {})

                # calculate total GPUs across resourceGroups/flavors
                total_gpu = 0
                for rg in spec.get("resourceGroups", []) or []:
                    for flav in rg.get("flavors", []) or []:
                        for res in flav.get("resources", []) or []:
                            if res.get("name") == "nvidia.com/gpu":
                                try:
                                    total_gpu += int(res.get("nominalQuota", 0))
                                except (TypeError, ValueError):
                                    continue

                admitted = status.get("admittedWorkloads", 0)
                pending = status.get("pendingWorkloads", 0)
                reserving = status.get("reservingWorkloads", 0)
                queueing = spec.get("queueingStrategy", "")

                print(
                    f"{meta.get('name', '')}\t"
                    f"admitted: {admitted}\t"
                    f"pending: {pending}\t"
                    f"reserved: {reserving}\t"
                    f"GPUs: {total_gpu}\t"
                    f"{queueing}"
                )

        except oc.OpenShiftPythonException as e:
            sys.exit(f"Error occurred while retrieving ClusterQueues: {e}")
