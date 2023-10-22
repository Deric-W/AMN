#!/usr/bin/python3

"""Virtual machines for the AMN instructions sets"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from enum import EnumMeta
from collections.abc import Iterator, Iterable, Sequence, Mapping
from typing import Type, TypeVar, Generic

__version__ = "0.6.1"
__author__  = "Eric Niklas Wolf"
__email__   = "eric_niklas.wolf@mailbox.tu-dresden.de"
__all__ = (
    "am0",
    "am1",
    "repl",
    "main",
    "AbstractEnumMeta",
    "AbstractInstruction",
    "AbstractMachine"
)

T = TypeVar("T")
I = TypeVar("I")


class AbstractEnumMeta(EnumMeta, ABCMeta):
    """Workaround to create enum extends an abc"""


class AbstractInstruction(Generic[T], metaclass=ABCMeta):
    """Instruction for an abstract machine"""

    @classmethod
    @abstractmethod
    def parse(cls, line: str) -> T:
        """parse an instance with payload from a line"""
        raise NotImplementedError()

    @classmethod
    def parse_program(cls, source: str) -> Iterator[T]:
        """parse a program consisting of multiple lines"""
        for number, line in enumerate(source.split("\n"), start=1):
            line = line.rstrip()
            if line.endswith(";"):
                try:
                    instruction = cls.parse(line[:-1])
                except KeyError as error:
                    raise ValueError(f"invalid instruction at line {number}") from error
                except ValueError as error:
                    raise ValueError(f"invalid payload at line {number}") from error
                except Exception as error:
                    raise ValueError(f"error while parsing line {number}") from error
                else:
                    yield instruction
            elif line:
                raise ValueError(f"missing semicolon on line {number}")
            else:
                continue


class AbstractMachine(Generic[I], metaclass=ABCMeta):
    """Abstract virtual machine for instructions"""

    __slots__ = ("counter",)

    counter: int

    @classmethod
    @abstractmethod
    def default(cls: Type[T], input: Iterator[int]) -> T:
        """create an instance in the default state"""
        raise NotImplementedError()

    def status(self) -> Mapping[str, object]:
        """return an object mapping values to visualisations"""
        return {"Counter: ": self.counter}

    @abstractmethod
    def state(self, input: Iterable[int], output: Iterable[int]) -> str:
        """create a string representation of the current machine state"""
        raise NotImplementedError()

    @abstractmethod
    def execute_instruction(self, instruction: I) -> int | None:
        """execute an instruction, returning the output if produced"""
        raise NotImplementedError()

    def execute_program(self, program: Sequence[I]) -> Iterator[int | None]:
        """execute a program, yielding after every instruction"""
        self.counter = 1
        while 0 < self.counter <= len(program):
            yield self.execute_instruction(program[self.counter - 1])

    @abstractmethod
    def reset(self) -> None:
        """reset the machine to the default state"""
        raise NotImplementedError()
