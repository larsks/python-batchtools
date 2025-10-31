# pyright: reportExplicitAny=false, reportAny=false

import abc
from typing import Protocol
from typing import Any
from typing_extensions import override

import argparse


class SubParserFactory(Protocol):
    """
    This is here to make type checkers happy. Since argparse._SubParsersAction
    is a private class, we can't use it as a type hint, so we use this instead.
    """

    def add_parser(
        self,
        name: str,
        *,
        deprecated: bool = False,
        **kwargs: Any,
    ) -> argparse.ArgumentParser: ...


class ArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Provide the behavior of both argparse.ArgumentDefaultsHelpFormatter
    and argparse.RawDescriptionHelpFormatter. This means that argparse will
    care of documenting default values for us, and it won't reformat our
    carefully crafted help text."""

    @override
    def _fill_text(
        self, text: str, width: int | None = None, indent: str | None = None
    ):
        return "".join(indent + line for line in text.splitlines(keepends=True))


class Command(abc.ABC):
    """
    Base class for all command implementations.
    """

    name: str
    help: str
    description: str | None = None

    @classmethod
    def build_parser(cls, subparsers: SubParserFactory) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            cls.name,
            help=cls.help,
            description=cls.__doc__,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )

        return p

    @staticmethod
    @abc.abstractmethod
    def run(args: argparse.Namespace) -> None:
        raise NotImplementedError()
