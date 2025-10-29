from typing import Any
from typing import Callable
from unittest import mock


def DictToObject(
    spec: dict[str, Any], obj: mock.Mock | None = None, name: str = None
) -> mock.Mock:
    """Transform a nested dictionary into an object hiearchy. We use this to create fake
    openshift_client response objects."""

    if obj is None:
        obj = mock.Mock(spec=list(spec.keys()), name=name)

    for key, val in spec.items():
        if isinstance(val, dict):
            setattr(obj, key, DictToObject(val, getattr(obj, key)))
        elif isinstance(val, list):
            setattr(
                obj,
                key,
                list(
                    [
                        DictToObject(item) if isinstance(item, dict) else item
                        for item in val
                    ]
                ),
            )
        elif isinstance(val, tuple) and len(val) > 0 and isinstance(val[0], Callable):
            if len(val) > 1:
                for k, v in val[1].items():
                    setattr(getattr(obj, key), k, v)
        else:
            setattr(obj, key, val)

    return obj


def equalish(a: Any, b: Any) -> bool:
    """Compare two values for approximate equality.

    When comparing values, equalish treats the ellipsis (...) as as a wildcard.
    This means that the following comparisons return True:

    equalish('alice', ...)

    equalish(1, ...)

    equalish(
        {'name': 'alice', 'color': 'blue'},
        {'name': 'alice', 'color': ...},
    )

    equalish(
        [1, 2, ...],
        [1, 2, 3],
    )
    """
    if a is ... or b is ...:
        return True
    elif type(a) is not type(b):
        return False
    elif isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        for k in range(len(a)):
            if not equalish(a[k], b[k]):
                return False
    elif isinstance(a, dict):
        if len(a) != len(b):
            return False
        for k in a:
            if k not in b:
                return False
            if not equalish(a[k], b[k]):
                return False
    else:
        return a == b

    return True
