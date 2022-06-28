#!/usr/bin/python3

"""Virtual machines for the AMN instructions sets"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from enum import EnumMeta
from collections.abc import Iterator, Sequence, Mapping
from typing import Type, TypeVar, Generic

__version__ = "0.4.2"
__author__  = "Eric Niklas Wolf"
__email__   = "eric_niklas.wolf@mailbox.tu-dresden.de"
__all__ = (
    "am0",
    "am1",
    "repl",
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
            try:
                if not line or line.isspace():
                    continue
                yield cls.parse(line)
            except KeyError as error:
                raise ValueError(f"invalid instruction at line {number}") from error
            except ValueError as error:
                raise ValueError(f"invalid payload at line {number}") from error
            except Exception as error:
                raise ValueError(f"error while parsing line {number}") from error


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
    def execute_instruction(self, instruction: I) -> int | None:
        """execute an instruction, returning the output if produced"""
        raise NotImplementedError()

    def execute_program(self, program: Sequence[I]) -> Iterator[int]:
        """execute a program, yielding occuring output"""
        self.counter = 1
        while 0 < self.counter <= len(program):
            output = self.execute_instruction(program[self.counter - 1])
            if output is not None:
                yield output

    @abstractmethod
    def reset(self) -> None:
        """reset the machine to the default state"""
        raise NotImplementedError()
