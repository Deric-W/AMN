"""Simple virtual machine for the AM1 instruction set"""

from __future__ import annotations

import re
from enum import Enum, unique
from itertools import repeat
from typing import TYPE_CHECKING

from . import (
    AbstractEnumMeta,
    AbstractInstruction,
    AbstractMachine,
    ExecutionError,
    InvalidInstructionError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence


__all__ = ("Instruction", "Machine", "MemoryContext")

INSTRUCTION_PATTERN = re.compile(r"([A-Z]{2,6})(\((.*)\)|( .*))?")


@unique
class MemoryContext(Enum):
    """Context relative to which an index should be loaded"""

    GLOBAL = 0
    LOKAL = 1

    def resolve_address(self, address: int, reference_pointer: int) -> int:
        """resolve an relative address to a absolute one"""
        if self is MemoryContext.LOKAL:
            address += reference_pointer
        if address <= 0:
            msg = f"address {address} references outside the runtime stack (reference pointer: {reference_pointer})"
            raise ValueError(msg)
        return address


@unique
class Instruction(
    AbstractInstruction[tuple["Instruction", MemoryContext, int]], Enum, metaclass=AbstractEnumMeta
):
    """AM1 instruction"""

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
    LOADA = 13
    LOADI = 14
    STORE = 15
    STOREI = 16
    LIT = 17
    JMP = 18
    JMC = 19
    WRITE = 20
    WRITEI = 21
    READ = 22
    READI = 23
    PUSH = 24
    CALL = 25
    INIT = 26
    RET = 27

    @classmethod
    def parse(cls, line: str) -> tuple[Instruction, MemoryContext, int]:
        """
        Parse an instance from a line like '<Name> <payload>', '<Name>' or '<Name>(context, payload)'.

        Raises a InvalidInstructionError when the parsing fails.
        """
        match = INSTRUCTION_PATTERN.fullmatch(line)
        if match is None:
            reason = "invalid instruction"
            raise InvalidInstructionError(reason, line)
        name = match.group(1)
        args = match.group(3)
        arg = match.group(4)
        try:
            instruction = cls[name]
        except KeyError as error:
            reason = "invalid instruction"
            raise InvalidInstructionError(reason, line) from error
        if args is not None:
            first, sep, last = args.partition(",")
            if sep == "":
                context = MemoryContext.LOKAL
                payload = first
            else:
                try:
                    context = MemoryContext[first.upper()]
                except KeyError as error:
                    reason = "invalid context"
                    raise InvalidInstructionError(reason, line) from error
                payload = last
        elif arg is not None:
            context = MemoryContext.LOKAL
            payload = arg
        else:
            return (instruction, MemoryContext.LOKAL, 0)
        try:
            number_payload = int(payload)
        except ValueError as error:
            reason = "invalid payload"
            raise InvalidInstructionError(reason, line) from error
        return (instruction, context, number_payload)

    def is_jump(self) -> bool:
        """check if the instruction is a jump"""
        return self.value in {18, 19, 25, 27}

    def has_payload(self) -> bool:
        """check if the instruction uses its payload"""
        return self.value >= Instruction.LOAD.value and self is not Instruction.PUSH

    def has_context(self) -> bool:
        """check if the instruction has a context"""
        return self in (
            Instruction.LOAD,
            Instruction.LOADA,
            Instruction.STORE,
            Instruction.READ,
            Instruction.WRITE,
        )


class Machine(AbstractMachine[tuple[Instruction, MemoryContext, int]]):
    """machine for executing AM0 instructions"""

    __slots__ = ("input", "reference_pointer", "runtime_stack", "stack")

    stack: list[int]

    runtime_stack: list[int]

    reference_pointer: int

    input: Iterator[int]

    def __init__(
        self,
        counter: int,
        stack: list[int],
        runtime_stack: list[int],
        reference_pointer: int,
        input: Iterator[int],  # noqa: A002
    ) -> None:
        self.counter = counter
        self.stack = stack
        self.runtime_stack = runtime_stack
        self.reference_pointer = reference_pointer
        self.input = input

    @classmethod
    def default(cls, input: Iterator[int]) -> Machine:  # noqa: A002
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
            "Reference Pointer": self.reference_pointer,
        }

    def frames(self) -> Iterator[Sequence[int]]:
        """
        Yield the runtime stack split into call frames from latest to first.
        Parameters are part of the previous frame!
        """
        previous_reference = len(self.runtime_stack) + 2
        reference = self.reference_pointer
        while reference > 0:
            yield self.runtime_stack[reference - 2 : previous_reference - 2]
            previous_reference, reference = reference, self.runtime_stack[reference - 1]
        if previous_reference > 2:  # noqa: PLR2004
            yield self.runtime_stack[: previous_reference - 2]

    def state(self, input: Iterable[int], output: Iterable[int]) -> str:  # noqa: A002
        """create a string representation of the current machine state"""
        return (
            f"({self.counter}, "
            f"{' : '.join(map(str, reversed(self.stack))):ε<1}, "
            f"{' : '.join(map(str, self.runtime_stack)):ε<1}, "
            f"{self.reference_pointer}, "
            f"{' : '.join(map(str, input)):ε<1}, "
            f"{' : '.join(map(str, output)):ε<1})"
        )

    def execute_instruction(
        self, instruction: tuple[Instruction, MemoryContext, int]
    ) -> int | None:
        """
        Execute an instruction, returning the output if produced.

        Raises ExecutionError if the instruction could not be executed.
        """
        value = None
        opcode = instruction[0]
        match instruction:
            case (Instruction.ADD, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] + self.stack[-1]
                self.stack.pop()
            case (Instruction.MUL, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] * self.stack[-1]
                self.stack.pop()
            case (Instruction.SUB, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] - self.stack[-1]
                self.stack.pop()
            case (Instruction.DIV, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] // self.stack[-1]
                self.stack.pop()
            case (Instruction.MOD, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = self.stack[-2] % self.stack[-1]
                self.stack.pop()
            case (Instruction.EQ, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] == self.stack[-1])
                self.stack.pop()
            case (Instruction.NE, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] != self.stack[-1])
                self.stack.pop()
            case (Instruction.LT, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] < self.stack[-1])
                self.stack.pop()
            case (Instruction.GT, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] > self.stack[-1])
                self.stack.pop()
            case (Instruction.LE, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] <= self.stack[-1])
                self.stack.pop()
            case (Instruction.GE, _, _):
                self._assert_stack(2, opcode)
                self.stack[-2] = int(self.stack[-2] >= self.stack[-1])
                self.stack.pop()
            case (Instruction.LOAD, context, address):
                addr = self._resolve_runtime_stack(context, address, opcode)
                self.stack.append(self._load_runtime_stack(addr, opcode))
            case (Instruction.LOADA, context, address):
                addr = self._resolve_runtime_stack(context, address, opcode)
                self.stack.append(addr)
            case (Instruction.LOADI, _, address):
                addr = self._resolve_runtime_stack(MemoryContext.LOKAL, address, opcode)
                addr = self._load_runtime_stack(addr, opcode)
                self.stack.append(self._load_runtime_stack(addr, opcode))
            case (Instruction.STORE, context, address):
                self._assert_stack(1, opcode)
                addr = self._resolve_runtime_stack(context, address, opcode)
                self._assert_runtime_stack(addr, opcode)
                self.runtime_stack[addr - 1] = self.stack.pop()
            case (Instruction.STOREI, _, address):
                self._assert_stack(1, opcode)
                addr = self._resolve_runtime_stack(MemoryContext.LOKAL, address, opcode)
                addr = self._load_runtime_stack(addr, opcode)
                self._assert_runtime_stack(addr, opcode)
                self.runtime_stack[addr - 1] = self.stack.pop()
            case (Instruction.LIT, _, literal):
                self.stack.append(literal)
            case (Instruction.JMP, _, counter):
                self.counter = counter - 1
            case (Instruction.JMC, _, counter):
                self._assert_stack(1, opcode)
                if self.stack.pop() == 0:
                    self.counter = counter - 1
            case (Instruction.WRITE, context, address):
                addr = self._resolve_runtime_stack(context, address, opcode)
                value = self._load_runtime_stack(addr, opcode)
            case (Instruction.WRITEI, _, address):
                addr = self._resolve_runtime_stack(MemoryContext.LOKAL, address, opcode)
                addr = self._load_runtime_stack(addr, opcode)
                value = self._load_runtime_stack(addr, opcode)
            case (Instruction.READ, context, address):
                addr = self._resolve_runtime_stack(context, address, opcode)
                self._assert_runtime_stack(addr, opcode)
                self.runtime_stack[addr - 1] = self._consume_input(opcode)
            case (Instruction.READI, _, address):
                addr = self._resolve_runtime_stack(MemoryContext.LOKAL, address, opcode)
                addr = self._load_runtime_stack(addr, opcode)
                self._assert_runtime_stack(addr, opcode)
                self.runtime_stack[addr - 1] = self._consume_input(opcode)
            case (Instruction.PUSH, _, _):
                self._assert_stack(1, opcode)
                self.runtime_stack.append(self.stack.pop())
            case (Instruction.CALL, _, counter):
                self.runtime_stack.append(self.counter + 1)
                self.runtime_stack.append(self.reference_pointer)
                self.counter = counter - 1
                self.reference_pointer = len(self.runtime_stack)
            case (Instruction.INIT, _, variables):
                self.runtime_stack.extend(repeat(0, variables))
            case (Instruction.RET, _, parameters) if self.reference_pointer > 1:
                self._assert_runtime_stack(self.reference_pointer - 1, opcode)
                self._assert_runtime_stack(self.reference_pointer, opcode)
                old_reference = self.reference_pointer
                self.counter = self.runtime_stack[self.reference_pointer - 2] - 1
                self.reference_pointer = self.runtime_stack[self.reference_pointer - 1]
                del self.runtime_stack[old_reference - parameters - 2 :]
            case (Instruction.RET, _, _):
                reason = "stack is too small to return"
                raise ExecutionError(reason, opcode)
            case _ as invalid:
                raise ExecutionError("invalid instruction", invalid)  # noqa: EM101, TRY003
        self.counter += 1
        return value

    def _assert_stack(self, depth: int, instruction: Instruction) -> None:
        if len(self.stack) < depth:
            reason = f"not enough values on the stack, {depth} required"
            raise ExecutionError(reason, instruction)

    def _assert_runtime_stack(self, address: int, instruction: Instruction) -> None:
        if not 1 <= address <= len(self.runtime_stack):
            reason = f"invalid memory address: {address}"
            raise ExecutionError(reason, instruction)

    def _resolve_runtime_stack(
        self, context: MemoryContext, address: int, instruction: Instruction
    ) -> int:
        try:
            return context.resolve_address(address, self.reference_pointer)
        except ValueError as error:
            raise ExecutionError(error.args[0], instruction) from None

    def _load_runtime_stack(self, address: int, instruction: Instruction) -> int:
        try:
            return self.runtime_stack[address - 1]
        except IndexError as error:
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
        self.runtime_stack.clear()
        self.reference_pointer = 0
