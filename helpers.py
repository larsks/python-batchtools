import openshift_client as oc


def is_logged_in() -> bool:
    try:
        oc.invoke("whoami")
        return True
    except oc.OpenShiftPythonException:
        return False


def pretty_print(pod: oc.APIObject) -> str:
    formatted_logs: str = ""
    try:
        logs: dict[str, str] = pod.logs()
        # ⋆ ˚｡⋆୨୧˚ stringify and pretty print for readibility ⋆ ˚｡⋆୨୧˚
        formatted_logs = str(logs).replace("\\n", "\n")
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while retrieving logs: {e}")

    return formatted_logs


def oc_delete(job_name: str) -> None:
    try:
        print(f"Deleting {job_name}")
        oc.invoke("delete", ["job", job_name])
    except oc.OpenShiftPythonException as e:
        print(f"Error occurred while deleting job: {e}")
