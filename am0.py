#!/usr/bin/python3

"""Simple virtual machine for the AM0 instruction set"""

from __future__ import annotations
from collections.abc import Mapping, Iterator
from enum import Enum, unique
from . import AbstractEnumMeta, AbstractInstruction, AbstractMachine


__all__ = (
    "Instruction",
    "Machine"
)


@unique
class Instruction(AbstractInstruction[tuple["Instruction", int]], Enum, metaclass=AbstractEnumMeta):
    """AM0 instruction"""

    ADD   = 1
    MUL   = 2
    SUB   = 3
    DIV   = 4
    MOD   = 5
    EQ    = 6
    NE    = 7
    LT    = 8
    GT    = 9
    LE    = 10
    GE    = 11
    LOAD  = 12
    STORE = 13
    LIT   = 14
    JMP   = 15
    JMC   = 16
    WRITE = 17
    READ  = 18

    @classmethod
    def parse(cls, line: str) -> tuple[Instruction, int]:
        """parse an instance from a line like '<Name> <payload>' or '<Name>'"""
        name, seperator, payload = line.partition(" ")
        if seperator == "":
            return (cls[name], 0)
        else:
            return (cls[name], int(payload))

    def is_jump(self) -> bool:
        """check if the instruction is a jump"""
        return 14 < self.value < 17

    def has_payload(self) -> bool:
        """check if the instruction uses its payload"""
        return self.value > 11


class Machine(AbstractMachine[tuple[Instruction, int]]):
    """machine for executing AM0 instructions"""

    __slots__ = ("stack", "memory", "input")

    stack: list[int]

    memory: dict[int, int]

    input: Iterator[int]

    def __init__(self, counter: int, stack: list[int], memory: dict[int, int], input: Iterator[int]) -> None:
        self.counter = counter
        self.stack = stack
        self.memory = memory
        self.input = input

    @classmethod
    def default(cls, input: Iterator[int]) -> Machine:
        """create an instance with default values"""
        return cls(1, [], {}, input)

    def status(self) -> Mapping[str, object]:
        """return an object mapping values to visualisations"""
        memory = "\n" + "\n".join(f"\t{key} := {value}" for key, value in self.memory.items())
        return {
            "Counter": self.counter,
            "Stack": self.stack,
            "Memory": memory
        }

    def execute_instruction(self, instruction: tuple[Instruction, int]) -> int | None:
        """execute an instruction, returning the output if produced"""
        value = None
        match instruction:
            case (Instruction.ADD, _):
                self.stack[-2] = self.stack[-2] + self.stack[-1]
                self.stack.pop()
            case (Instruction.MUL, _):
                self.stack[-2] = self.stack[-2] * self.stack[-1]
                self.stack.pop()
            case (Instruction.SUB, _):
                self.stack[-2] = self.stack[-2] - self.stack[-1]
                self.stack.pop()
            case (Instruction.DIV, _):
                self.stack[-2] = self.stack[-2] // self.stack[-1]
                self.stack.pop()
            case (Instruction.MOD, _):
                self.stack[-2] = self.stack[-2] % self.stack[-1]
                self.stack.pop()
            case (Instruction.EQ, _):
                self.stack[-2] = self.stack[-2] == self.stack[-1]
                self.stack.pop()
            case (Instruction.NE, _):
                self.stack[-2] = self.stack[-2] != self.stack[-1]
                self.stack.pop()
            case (Instruction.LT, _):
                self.stack[-2] = self.stack[-2] < self.stack[-1]
                self.stack.pop()
            case (Instruction.GT, _):
                self.stack[-2] = self.stack[-2] > self.stack[-1]
                self.stack.pop()
            case (Instruction.LE, _):
                self.stack[-2] = self.stack[-2] <= self.stack[-1]
                self.stack.pop()
            case (Instruction.GE, _):
                self.stack[-2] = self.stack[-2] >= self.stack[-1]
                self.stack.pop()
            case (Instruction.LOAD, n):
                self.stack.append(self.memory[n])
            case (Instruction.STORE, n):
                self.memory[n] = self.stack.pop()
            case (Instruction.LIT, n):
                self.stack.append(n)
            case (Instruction.JMP, n):
                self.counter = n - 1
            case (Instruction.JMC, n):
                if self.stack.pop() == 0:
                    self.counter = n - 1
            case (Instruction.WRITE, n):
                value = self.memory[n]
            case (Instruction.READ, n):
                self.memory[n] = next(self.input)
            case i:
                raise ValueError(f"invalid instruction: '{i}'")
        self.counter += 1
        return value

    def reset(self) -> None:
        """reset the machine to the default state"""
        self.counter = 1
        self.stack.clear()
        self.memory.clear()
