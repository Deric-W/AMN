#!/usr/bin/python3

"""AMN REPL"""

from __future__ import annotations
from cmd import Cmd
from typing import Type, TypeVar, Generic, Any
from . import AbstractInstruction, AbstractMachine

__all__ = (
    "REPL",
)

T = TypeVar("T")


class REPL(Generic[T], Cmd):
    """interactive REPL"""

    instruction: Type[AbstractInstruction[T]]

    machine: AbstractMachine[T]

    def __init__(self, instruction: Type[AbstractInstruction[T]], machine: AbstractMachine[T], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.instruction = instruction
        self.machine = machine
        self.prompt = "AMN >> "

    def emptyline(self) -> bool:
        """ignore empty lines"""
        return False

    def do_exec(self, arg: str) -> bool:
        """execute an instruction"""
        try:
            instruction = self.instruction.parse(arg)
        except Exception as error:
            self.stdout.write(f"Error while parsing: {error!r}\n")
        else:
            try:
                output = self.machine.execute_instruction(instruction)
            except (LookupError, ValueError) as error:
                self.stdout.write(f"Error while executing: {error!r}\n")
            else:
                if output is not None:
                    self.stdout.write(f"Output: {output}\n")
        return False

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

    def default(self, line: str) -> None:
        """print an error"""
        self.stdout.write(f"*** Unknown command: {line}\n")

    def do_EOF(self, arg: str) -> bool:
        """exit the repl"""
        return self.do_exit(arg)

    def do_exit(self, _: object) -> bool:
        """exit the repl"""
        self.stdout.write("Exiting REPL...\n")
        return True
