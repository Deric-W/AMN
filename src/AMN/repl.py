"""AMN REPL"""

from __future__ import annotations

from cmd import Cmd
from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar

from . import AbstractInstruction, AbstractMachine, ExecutionError, InvalidInstructionError

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__: Final = ("REPL",)

T = TypeVar("T")


class REPL(Cmd, Generic[T]):
    """interactive REPL"""

    instruction: type[AbstractInstruction[T]]

    machine: AbstractMachine[T]

    def __init__(
        self,
        instruction: type[AbstractInstruction[T]],
        machine: AbstractMachine[T],
        instruction_set: str = "AMN",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.instruction = instruction
        self.machine = machine
        self.prompt = f"{instruction_set} >> "
        self.intro = f"Welcome the the {instruction_set} REPL, type 'help' for help"

    def emptyline(self) -> bool:
        """ignore empty lines"""
        return False

    def do_exec(self, arg: str) -> bool:
        """execute an instruction"""
        try:
            instruction = self.instruction.parse(arg)
        except InvalidInstructionError as error:
            self.stdout.write(f"Error while parsing: {error.reason}\n")
        else:
            try:
                output = self.machine.execute_instruction(instruction)
            except ExecutionError as error:
                self.stdout.write(f"Error while executing: {error.reason}\n")
            else:
                if output is not None:
                    self.stdout.write(f"Output: {output}\n")
        return False

    def complete_exec(self, text: str, line: str, begidx: int, endidx: int) -> Sequence[str]:  # noqa: ARG002
        """Complete arguments for the exec command."""
        prefix_length = 0
        while prefix_length < len(line):
            char = line[prefix_length]
            if char not in self.identchars:
                break
            prefix_length += 1
        while prefix_length < len(line):
            char = line[prefix_length]
            if not char.isspace():
                break
            prefix_length += 1
        results = self.instruction.complete_instruction(line[prefix_length:])
        return [result[begidx - prefix_length :] for result in results]

    def do_reset(self, _: object) -> bool:
        """reset the machine"""
        self.machine.reset()
        return False

    def do_status(self, _: object) -> bool:
        """print the current status of the machine"""
        for key, value in self.machine.status().items():
            self.stdout.write(f"{key}: {value}\n")
        return False

    def do_state(self, _: object) -> bool:
        """print the current state of the machine (inputs and outputs are always empty)"""
        self.stdout.write(f"{self.machine.state([], [])}\n")
        return False

    def do_EOF(self, arg: str) -> bool:  # noqa: N802
        """exit the repl"""
        return self.do_exit(arg)

    def do_exit(self, _: object) -> bool:
        """exit the repl"""
        self.stdout.write("Exiting REPL...\n")
        return True
