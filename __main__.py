#!/usr/bin/python3

"""Execute the module"""

from argparse import ArgumentParser, FileType
from itertools import repeat
from . import __doc__, __version__
from .am0 import Instruction, Machine
from .repl import REPL

ARGUMENT_PARSER = ArgumentParser(description=__doc__)
ARGUMENT_PARSER.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"%(prog)s {__version__}"
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
    machine = Machine.default(map(int, map(input, repeat("Input: "))))
    if args.file is None:
        REPL(Instruction, machine).cmdloop("Welcome the the AM0 REPL, type 'help' for help")
    else:
        program = tuple(Instruction.parse_program(args.file.read()))
        for output in machine.execute_program(program):
            if output is not None:
                print(f"Output: {output}")
