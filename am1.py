#!/usr/bin/python3

"""Simple virtual machine for the AM1 instruction set"""

from __future__ import annotations
from collections.abc import Mapping, Iterator
from enum import Enum, unique
import re
from itertools import repeat
from . import AbstractEnumMeta, AbstractInstruction, AbstractMachine


__all__ = (
    "MemoryContext",
    "Instruction",
    "Machine"
)

INSTRUCTION_PATTERN = re.compile(r"([A-Z]{2,6})(\((.*)\)|( .*))?")


@unique
class MemoryContext(Enum):
    """Context relative to which an index should be loaded"""

    GLOBAL = 0
    LOCAL  = 1

    def resolve_address(self, address: int, reference_pointer: int) -> int:
        """resolve an relative address to a absolute one"""
        if self is MemoryContext.LOCAL:
            address += reference_pointer
        if address <= 0:
            raise ValueError(
                f"address {address} references outside the runtime stack (reference pointer: {reference_pointer})"
            )
        return address


@unique
class Instruction(AbstractInstruction[tuple["Instruction", MemoryContext, int]], Enum, metaclass=AbstractEnumMeta):
    """AM1 instruction"""

    ADD    = 1
    MUL    = 2
    SUB    = 3
    DIV    = 4
    MOD    = 5
    EQ     = 6
    NE     = 7
    LT     = 8
    GT     = 9
    LE     = 10
    GE     = 11
    LOAD   = 12
    LOADA  = 13
    LOADI  = 14
    STORE  = 15
    STOREI = 16
    LIT    = 17
    JMP    = 18
    JMC    = 19
    WRITE  = 20
    WRITEI = 21
    READ   = 22
    READI  = 23
    PUSH   = 24
    CALL   = 25
    INIT   = 26
    RET    = 27

    @classmethod
    def parse(cls, line: str) -> tuple[Instruction, MemoryContext, int]:
        """parse an instance from a line like '<Name> <payload>', '<Name>' or '<Name>(context, payload)'"""
        match = INSTRUCTION_PATTERN.fullmatch(line)
        if match is None:
            raise KeyError("invalid instruction")
        name = match.group(1)
        args = match.group(3)
        arg = match.group(4)
        if args is not None:
            first, sep, last = args.partition(",")
            if sep == "":
                return (cls[name], MemoryContext.LOCAL, int(first))
            else:
                return (cls[name], MemoryContext[first.upper()], int(last))
        elif arg is not None:
            return (cls[name], MemoryContext.LOCAL, int(arg))
        else:
            return (cls[name], MemoryContext.LOCAL, 0)

    def is_jump(self) -> bool:
        """check if the instruction is a jump"""
        return 17 < self.value < 30

    def has_payload(self) -> bool:
        """check if the instruction uses its payload"""
        return self.value > 11 and self is not Instruction.PUSH

    def has_context(self) -> bool:
        """check if the instruction has a context"""
        return self in (
            Instruction.LOAD,
            Instruction.LOADA,
            Instruction.STORE,
            Instruction.READ,
            Instruction.WRITE
        )


class Machine(AbstractMachine[tuple[Instruction, MemoryContext, int]]):
    """machine for executing AM0 instructions"""

    __slots__ = ("stack", "runtime_stack", "reference_pointer", "input")

    stack: list[int]

    runtime_stack: list[int]

    reference_pointer: int

    input: Iterator[int]

    def __init__(self, counter: int, stack: list[int], runtime_stack: list[int], reference_pointer: int, input: Iterator[int]) -> None:
        self.counter = counter
        self.stack = stack
        self.runtime_stack = runtime_stack
        self.reference_pointer = reference_pointer
        self.input = input

    @classmethod
    def default(cls, input: Iterator[int]) -> Machine:
        """create an instance with default values"""
        return cls(1, [], [], 0, input)

    def status(self) -> Mapping[str, object]:
        """return an object mapping values to visualisations"""
        memory = "\n" + "\n".join(
            f"\t{key} := {value}" for key, value in enumerate(self.runtime_stack, start=1)
        )
        return {
            "Counter": self.counter,
            "Stack": self.stack,
            "Runtime Stack": memory,
            "Reference Pointer": self.reference_pointer
        }

    def execute_instruction(self, instruction: tuple[Instruction, MemoryContext, int]) -> int | None:
        """execute an instruction, returning the output if produced"""
        value = None
        match instruction:
            case (Instruction.ADD, _, _):
                self.stack[-2] = self.stack[-2] + self.stack[-1]
                self.stack.pop()
            case (Instruction.MUL, _, _):
                self.stack[-2] = self.stack[-2] * self.stack[-1]
                self.stack.pop()
            case (Instruction.SUB, _, _):
                self.stack[-2] = self.stack[-2] - self.stack[-1]
                self.stack.pop()
            case (Instruction.DIV, _, _):
                self.stack[-2] = self.stack[-2] // self.stack[-1]
                self.stack.pop()
            case (Instruction.MOD, _, _):
                self.stack[-2] = self.stack[-2] % self.stack[-1]
                self.stack.pop()
            case (Instruction.EQ, _, _):
                self.stack[-2] = self.stack[-2] == self.stack[-1]
                self.stack.pop()
            case (Instruction.NE, _, _):
                self.stack[-2] = self.stack[-2] != self.stack[-1]
                self.stack.pop()
            case (Instruction.LT, _, _):
                self.stack[-2] = self.stack[-2] < self.stack[-1]
                self.stack.pop()
            case (Instruction.GT, _, _):
                self.stack[-2] = self.stack[-2] > self.stack[-1]
                self.stack.pop()
            case (Instruction.LE, _, _):
                self.stack[-2] = self.stack[-2] <= self.stack[-1]
                self.stack.pop()
            case (Instruction.GE, _, _):
                self.stack[-2] = self.stack[-2] >= self.stack[-1]
                self.stack.pop()
            case (Instruction.LOAD, context, address):
                index = context.resolve_address(address, self.reference_pointer) - 1
                self.stack.append(self.runtime_stack[index])
            case (Instruction.LOADA, context, address):
                self.stack.append(context.resolve_address(address, self.reference_pointer))
            case (Instruction.LOADI, _, address):
                index = MemoryContext.LOCAL.resolve_address(address, self.reference_pointer) - 1
                self.stack.append(self.runtime_stack[self.runtime_stack[index] - 1])
            case (Instruction.STORE, context, address):
                self.runtime_stack[context.resolve_address(address, self.reference_pointer) - 1] = self.stack.pop()
            case (Instruction.STOREI, _, address):
                index = MemoryContext.LOCAL.resolve_address(address, self.reference_pointer) - 1
                self.runtime_stack[self.runtime_stack[index] - 1] = self.stack.pop()
            case (Instruction.LIT, _, n):
                self.stack.append(n)
            case (Instruction.JMP, _, n):
                self.counter = n - 1
            case (Instruction.JMC, _, n):
                if self.stack.pop() == 0:
                    self.counter = n - 1
            case (Instruction.WRITE, context, address):
                index = context.resolve_address(address, self.reference_pointer) - 1
                value = self.runtime_stack[index]
            case (Instruction.WRITEI, _, address):
                index = MemoryContext.LOCAL.resolve_address(address, self.reference_pointer) - 1
                value = self.runtime_stack[self.runtime_stack[index] - 1]
            case (Instruction.READ, context, address):
                index = context.resolve_address(address, self.reference_pointer) - 1
                self.runtime_stack[index] = next(self.input)
            case (Instruction.READI, _, address):
                index = MemoryContext.LOCAL.resolve_address(address, self.reference_pointer) - 1
                self.runtime_stack[self.runtime_stack[index] - 1] = next(self.input)
            case (Instruction.PUSH, _, _):
                self.runtime_stack.append(self.stack.pop())
            case (Instruction.CALL, _, counter):
                self.runtime_stack.append(self.counter + 1)
                self.runtime_stack.append(self.reference_pointer)
                self.counter = counter - 1
                self.reference_pointer = len(self.runtime_stack)
            case (Instruction.INIT, _, variables):
                self.runtime_stack.extend(repeat(0, variables))
            case (Instruction.RET, _, variables) if self.reference_pointer > 1:
                self.counter = self.runtime_stack[self.reference_pointer - 2] - 1
                self.reference_pointer = self.runtime_stack[self.reference_pointer - 1]
                del self.runtime_stack[-variables - 2:]
            case (Instruction.RET, _, _):
                raise LookupError("stack is too small to return")
            case invalid:
                raise ValueError(f"invalid instruction: '{invalid}'")
        self.counter += 1
        return value

    def reset(self) -> None:
        """reset the machine to the default state"""
        self.counter = 1
        self.stack.clear()
        self.runtime_stack.clear()
        self.reference_pointer = 0
