"""Virtual machines for the AMN instructions sets"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import EnumMeta
from typing import TYPE_CHECKING, Final, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

__version__ = "0.6.1"
__author__  = "Eric Niklas Wolf"
__email__   = "eric_niklas.wolf@mailbox.tu-dresden.de"
__all__ = (
    "AbstractEnumMeta",
    "AbstractInstruction",
    "AbstractMachine",
    "ExecutionError",
    "InvalidInstructionError",
    "InvalidProgramError",
    "am0",
    "am1",
    "main",
    "repl"
)

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")
I = TypeVar("I")


class InvalidInstructionError(ValueError):
    """Exception raised when a instruction can not be parsed."""

    reason: Final[str]
    """The reason for the error."""

    line: Final[str]
    """The line which caused the error."""

    def __init__(self, reason: str, line: str) -> None:
        super().__init__(f"failed to parse instruction '{line}': {reason}")
        self.reason = reason
        self.line = line


class InvalidProgramError(ValueError):
    """Exception raised when a program can not be parsed."""

    reason: Final[str]
    """The reason for the error."""

    line: Final[str]
    """The line which caused the error."""

    line_number: Final[int]
    """The number of the line which caused the error."""

    def __init__(self, reason: str, line: str, line_number: int) -> None:
        super().__init__(
            f"error while parsing program at line {line_number} ('{line}'): {reason}"
        )
        self.reason = reason
        self.line = line
        self.line_number = line_number


class AbstractEnumMeta(EnumMeta, ABCMeta):
    """Workaround to create enum extends an abc"""


class AbstractInstruction(Generic[T_co], metaclass=ABCMeta):
    """Instruction for an abstract machine"""

    @classmethod
    @abstractmethod
    def parse(cls, line: str) -> T_co:
        """
        Parse an instance with payload from a line.

        Raises a InvalidInstructionError when the parsing fails.
        """
        raise NotImplementedError

    @classmethod
    def parse_program(cls, source: str) -> Iterator[T_co]:
        """
        Parse a program consisting of multiple lines.

        Raises a InvalidProgramError when the parsing fails.
        """
        for number, raw_line in enumerate(source.split("\n"), start=1):
            line = raw_line.rstrip()
            if line.endswith(";"):
                try:
                    instruction = cls.parse(line[:-1])
                except InvalidInstructionError as error:
                    raise InvalidProgramError(error.reason, error.line, number) from error
                yield instruction
            elif line:
                reason = "missing semicolon"
                raise InvalidProgramError(reason, line, number)


class ExecutionError(Exception):
    """Exception raised when executing an instruction fails."""

    reason: Final[str]
    """The reason for the error."""

    instruction: Final[AbstractInstruction[object]]
    """The instruction which caused the error."""

    def __init__(self, reason: str, instruction: AbstractInstruction[object]) -> None:
        super().__init__(f"error while executing {instruction}: {reason}")
        self.reason = reason
        self.instruction = instruction


class AbstractMachine(Generic[I], metaclass=ABCMeta):
    """Abstract virtual machine for instructions"""

    __slots__ = ("counter",)

    counter: int

    @classmethod
    @abstractmethod
    def default(cls: type[T], input: Iterator[int]) -> T:
        """create an instance in the default state"""
        raise NotImplementedError

    def status(self) -> Mapping[str, object]:
        """return an object mapping values to visualisations"""
        return {"Counter: ": self.counter}

    @abstractmethod
    def state(self, input: Iterable[int], output: Iterable[int]) -> str:
        """create a string representation of the current machine state"""
        raise NotImplementedError

    @abstractmethod
    def execute_instruction(self, instruction: I) -> int | None:
        """
        Execute an instruction, returning the output if produced.

        Raises ExecutionError if the instruction could not be executed.
        """
        raise NotImplementedError

    def execute_program(self, program: Sequence[I]) -> Iterator[int | None]:
        """
        Execute a program, yielding after every instruction.

        Raises ExecutionError if a instruction could not be executed.
        """
        self.counter = 1
        while 0 < self.counter <= len(program):
            yield self.execute_instruction(program[self.counter - 1])

    @abstractmethod
    def reset(self) -> None:
        """reset the machine to the default state"""
        raise NotImplementedError
