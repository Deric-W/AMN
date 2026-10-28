"""CLI commands"""

from __future__ import annotations

import sys
import traceback
from argparse import ArgumentParser, FileType, Namespace
from collections.abc import Iterator, Mapping, MutableSequence
from typing import Any, Final, TypeVar, cast

from . import AbstractInstruction, AbstractMachine, ExecutionError
from . import __doc__ as _doc
from . import __version__ as _version
from .am0 import Instruction as AM0Instruction
from .am0 import Machine as AM0Machine
from .am1 import Instruction as AM1Instruction
from .am1 import Machine as AM1Machine
from .repl import REPL

__all__: Final = ("ARGUMENT_PARSER", "MACHINES", "main")

T = TypeVar("T")

MACHINES: Final[Mapping[str, tuple[type[AbstractInstruction[Any]], type[AbstractMachine[Any]]]]] = {
    "AM0": (AM0Instruction, AM0Machine),
    "AM1": (AM1Instruction, AM1Machine),
}


class _StdinInput(Iterator[int]):
    _prompt: str

    def __init__(self, prompt: str = "Input: ") -> None:
        self._prompt = prompt

    def __next__(self) -> int:
        while True:
            try:
                value = input(self._prompt)
            except EOFError as error:
                raise StopIteration from error
            try:
                return int(value)
            except ValueError as error:
                print(f"Error while reading input: {error}")  # noqa: T201


class _ReplInput(Iterator[int]):
    _input: Iterator[int]

    def __init__(self, prompt: str = "Input: ") -> None:
        self._input = _StdinInput(prompt)

    def __next__(self) -> int:
        try:
            return next(self._input)
        except KeyboardInterrupt as error:
            raise StopIteration from error


def _sequence_input(sequence: MutableSequence[int]) -> Iterator[int]:
    while len(sequence) > 0:
        yield sequence.pop()


def main() -> int:
    """CLI entry point"""
    args = ARGUMENT_PARSER.parse_args()
    instruction, machine = MACHINES[args.instructions.upper()]
    return cast("int", args.main(instruction, machine, args))


def main_repl(
    instruction: type[AbstractInstruction[T]], machine: type[AbstractMachine[T]], args: Namespace
) -> int:
    """entry point for the repl subcommand"""
    repl = REPL(instruction, machine.default(_ReplInput()), args.instructions.upper())
    repl.cmdloop()
    return 0


def main_exec(
    instruction: type[AbstractInstruction[T]], machine: type[AbstractMachine[T]], args: Namespace
) -> int:
    """entry point for the exec subcommand"""
    program = tuple(instruction.parse_program(args.file.read()))
    _input = _ReplInput() if args.interactive else _StdinInput()
    _machine = machine.default(_input)
    execution = _machine.execute_program(program)
    while True:
        try:
            output = next(execution)
        except StopIteration:
            break
        except ExecutionError:
            if args.interactive:
                traceback.print_exc()
                break
            raise
        if output is not None:
            print(f"Output: {output}")  # noqa: T201
    if args.interactive:
        repl = REPL(instruction, _machine, args.instructions.upper())
        repl.cmdloop()
    return 0


def main_trace(
    instruction: type[AbstractInstruction[T]], machine: type[AbstractMachine[T]], args: Namespace
) -> int:
    """entry point for the trace subcommand"""
    program = tuple(instruction.parse_program(args.file.read()))
    output: list[int] = []
    args.input.reverse()
    _machine = machine.default(_sequence_input(args.input))
    sys.stderr.write(f"{_machine.state(reversed(args.input), output)}\n")
    for value in _machine.execute_program(program):
        if value is not None:
            output.append(value)
        sys.stderr.write(f"{_machine.state(reversed(args.input), output)}\n")
    return 0


ARGUMENT_PARSER: Final = ArgumentParser(description=_doc)
ARGUMENT_PARSER.add_argument("-v", "--version", action="version", version=f"%(prog)s {_version}")
ARGUMENT_PARSER.add_argument(
    "-i",
    "--instructions",
    type=str,
    default="AM0",
    help=f"Instruction set to use, possible selections: {', '.join(MACHINES.keys())}",
)

SUBCOMMANDS: Final = ARGUMENT_PARSER.add_subparsers(required=True)

REPL_PARSER: Final = SUBCOMMANDS.add_parser(
    "repl", help="start the REPL (read evaluate print loop)"
)
REPL_PARSER.set_defaults(main=main_repl)

EXEC_PARSER: Final = SUBCOMMANDS.add_parser("exec", help="execute a program")
EXEC_PARSER.add_argument(
    "file",
    nargs="?",
    type=FileType("r"),
    default=sys.stdin,
    help="file to read instructions from (omit for stdin)",
)
EXEC_PARSER.add_argument(
    "-i", "--interactive", action="store_true", help="open the REPL after executing the program"
)
EXEC_PARSER.set_defaults(main=main_exec)

TRACE_PARSER: Final = SUBCOMMANDS.add_parser("trace", help="trace the execution of a program")
TRACE_PARSER.add_argument(
    "--input", nargs="*", type=int, default=[], help="input values for the program"
)
TRACE_PARSER.add_argument(
    "file",
    nargs="?",
    type=FileType("r"),
    default=sys.stdin,
    help="file to read instructions from (omit for stdin)",
)
TRACE_PARSER.set_defaults(main=main_trace)
