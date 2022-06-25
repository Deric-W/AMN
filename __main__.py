#!/usr/bin/python3

"""Execute the module"""

from typing import Type
from argparse import ArgumentParser, FileType
from itertools import repeat
from . import __doc__, __version__, AbstractInstruction, AbstractMachine
from .am0 import Instruction as AM0Instruction, Machine as AM0Machine
from .am1 import Instruction as AM1Instruction, Machine as AM1Machine
from .repl import REPL


MACHINES: dict[str, tuple[Type[AbstractInstruction], Type[AbstractMachine]]] = {
    "AM0": (AM0Instruction, AM0Machine),
    "AM1": (AM1Instruction, AM1Machine)
}

ARGUMENT_PARSER = ArgumentParser(description=__doc__)
ARGUMENT_PARSER.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"%(prog)s {__version__}"
)
ARGUMENT_PARSER.add_argument(
    "-i",
    "--instructions",
    type=str,
    default="AM0",
    help="Instruction set to use, possible selections: AM0, AM1"
)
ARGUMENT_PARSER.add_argument(
    "file",
    nargs="?",
    type=FileType("r"),
    default=None,
    help="path to program which shall be executed, omit for interactive REPL"
)

if __name__ == "__main__":
    args = ARGUMENT_PARSER.parse_args()
    Instruction, Machine = MACHINES[args.instructions.upper()]
    machine = Machine.default(map(int, map(input, repeat("Input: "))))
    if args.file is None:
        REPL(Instruction, machine).cmdloop(f"Welcome the the {args.instructions.upper()} REPL, type 'help' for help")
    else:
        program = tuple(Instruction.parse_program(args.file.read()))
        for output in machine.execute_program(program):
            print(f"Output: {output}")
