"""Simple virtual machine for the AM0 instruction set"""

from __future__ import annotations

from enum import Enum, unique
from typing import TYPE_CHECKING

from . import (
    AbstractEnumMeta,
    AbstractInstruction,
    AbstractMachine,
    ExecutionError,
    InvalidInstructionError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

__all__ = ("Instruction", "Machine")


@unique
class Instruction(AbstractInstruction[tuple["Instruction", int]], Enum, metaclass=AbstractEnumMeta):
    """AM0 instruction"""

    ADD = 1
    MUL = 2
    SUB = 3
    DIV = 4
    MOD = 5
    EQ = 6
    NE = 7
    LT = 8
    GT = 9
    LE = 10
    GE = 11
    LOAD = 12
    STORE = 13
    LIT = 14
    JMP = 15
    JMC = 16
    WRITE = 17
    READ = 18

    @classmethod
    def parse(cls, line: str) -> tuple[Instruction, int]:
        """
        Parse an instance from a line like '<Name> <payload>' or '<Name>'.

        Raises a InvalidInstructionError when the parsing fails.
        """
        name, seperator, payload = line.partition(" ")
        try:
            instruction = cls[name]
        except KeyError as error:
            reason = "invalid instruction"
            raise InvalidInstructionError(reason, line) from error
        if seperator == "":
            return (instruction, 0)
        try:
            number_payload = int(payload)
        except ValueError as error:
            reason = "invalid payload"
            raise InvalidInstructionError(reason, line) from error
        return (instruction, number_payload)

    def is_jump(self) -> bool:
        """check if the instruction is a jump"""
        return Instruction.JMP.value <= self.value <= Instruction.JMC.value

    def has_payload(self) -> bool:
        """check if the instruction uses its payload"""
        return self.value >= Instruction.LOAD.value


class Machine(AbstractMachine[tuple[Instruction, int]]):
    """machine for executing AM0 instructions"""

    __slots__ = ("input", "memory", "stack")

    stack: list[int]

    memory: dict[int, int]

    input: Iterator[int]

    def __init__(
        self,
        counter: int,
        stack: list[int],
        memory: dict[int, int],
        input: Iterator[int],  # noqa: A002
    ) -> None:
        self.counter = counter
        self.stack = stack
        self.memory = memory
        self.input = input

    @classmethod
    def default(cls, input: Iterator[int]) -> Machine:  # noqa: A002
        """create an instance with default values"""
        return cls(1, [], {}, input)

    def status(self) -> Mapping[str, object]:
        """return an object mapping values to visualisations"""
        memory = "\n" + "\n".join(f"\t{key} := {value}" for key, value in self.memory.items())
        return {"Counter": self.counter, "Stack": self.stack, "Memory": memory}

    def state(self, input: Iterable[int], output: Iterable[int]) -> str:  # noqa: A002
        """create a string representation of the current machine state"""
        memory = ", ".join(f"{key}/{value}" for key, value in self.memory.items())
        return (
            f"({self.counter}, "
            f"{' : '.join(map(str, reversed(self.stack))):ε<1}, "
            f"[{memory}], "
            f"{' : '.join(map(str, input)):ε<1}, "
            f"{' : '.join(map(str, output)):ε<1})"
        )

    def execute_instruction(self, instruction: tuple[Instruction, int]) -> int | None:
        """
        Execute an instruction, returning the output if produced.

        Raises ExecutionError if the instruction could not be executed.
        """
        value = None
        opcode = instruction[0]
        match instruction:
            case (Instruction.ADD, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] + self.stack[-1]
                self.stack.pop()
            case (Instruction.MUL, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] * self.stack[-1]
                self.stack.pop()
            case (Instruction.SUB, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] - self.stack[-1]
                self.stack.pop()
            case (Instruction.DIV, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] // self.stack[-1]
                self.stack.pop()
            case (Instruction.MOD, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] % self.stack[-1]
                self.stack.pop()
            case (Instruction.EQ, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] == self.stack[-1])
                self.stack.pop()
            case (Instruction.NE, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] != self.stack[-1])
                self.stack.pop()
            case (Instruction.LT, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] < self.stack[-1])
                self.stack.pop()
            case (Instruction.GT, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] > self.stack[-1])
                self.stack.pop()
            case (Instruction.LE, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] <= self.stack[-1])
                self.stack.pop()
            case (Instruction.GE, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] >= self.stack[-1])
                self.stack.pop()
            case (Instruction.LOAD, address):
                self.stack.append(self._load_memory(address, opcode))
            case (Instruction.STORE, address):
                self._assert_stack(1, opcode)
                self.memory[address] = self.stack.pop()
            case (Instruction.LIT, literal):
                self.stack.append(literal)
            case (Instruction.JMP, counter):
                self.counter = counter - 1
            case (Instruction.JMC, counter):
                self._assert_stack(1, opcode)
                if self.stack.pop() == 0:
                    self.counter = counter - 1
            case (Instruction.WRITE, address):
                value = self._load_memory(address, opcode)
            case (Instruction.READ, address):
                self.memory[address] = self._consume_input(opcode)
            case _ as invalid:
                raise ExecutionError("invalid instruction", invalid)  # noqa: EM101, TRY003
        self.counter += 1
        return value

    def _assert_stack(self, depth: int, instruction: Instruction) -> None:
        if len(self.stack) < depth:
            reason = f"not enough values on the stack, {depth} required"
            raise ExecutionError(reason, instruction)

    def _load_memory(self, address: int, instruction: Instruction) -> int:
        try:
            return self.memory[address]
        except KeyError as error:
            reason = f"invalid memory address: {address}"
            raise ExecutionError(reason, instruction) from error

    def _consume_input(self, instruction: Instruction) -> int:
        try:
            return next(self.input)
        except StopIteration as error:
            reason = "input iterator exhausted"
            raise ExecutionError(reason, instruction) from error

    def reset(self) -> None:
        """reset the machine to the default state"""
        self.counter = 1
        self.stack.clear()
        self.memory.clear()
