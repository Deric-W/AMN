#!/usr/bin/python3

"""REPL tests"""

from collections import deque
from collections.abc import Iterator
from io import StringIO
from unittest import TestCase
from AMN.am0 import Instruction, Machine
from AMN.repl import REPL


class ReplTest(TestCase):
    """REPL tests"""

    repl: REPL[tuple[Instruction, int]]

    input: deque[int]

    stdin: StringIO

    stdout: StringIO

    def setUp(self) -> None:
        self.input = deque()
        self.stdin = StringIO()
        self.stdout = StringIO()
        self.repl = REPL(
            Instruction,
            Machine.default(self.lazy_input()),
            stdin=self.stdin,
            stdout=self.stdout
        )
        self.repl.use_rawinput = False

    def lazy_input(self) -> Iterator[int]:
        """Lazy consume the input"""
        while True:
            try:
                yield self.input.pop()
            except IndexError:
                break

    def set_stdin(self, value: str) -> None:
        """Set the current stdin"""
        self.stdin.seek(0)
        self.stdin.truncate(0)
        self.stdin.write(value)
        self.stdin.seek(0)

    def reset_stdout(self) -> None:
        """Reset stdout"""
        self.stdout.seek(0)
        self.stdout.truncate(0)

    def test_emptyline(self) -> None:
        """Test the empty line"""
        self.set_stdin("\n")
        self.repl.cmdloop()
        self.assertEqual(
            self.stdout.getvalue(),
            f"{self.repl.prompt * 2}Exiting REPL...\n"
        )

    def test_exec(self) -> None:
        """Test the exec command"""
        self.set_stdin("exec sadasdasd\nexec SUB\n")
        self.repl.cmdloop()
        self.assertEqual(
            self.stdout.getvalue(),
            (
                f"{self.repl.prompt}Error while parsing: KeyError('sadasdasd')\n"
                f"{self.repl.prompt}Error while executing: IndexError('list index out of range')\n"
                f"{self.repl.prompt}Exiting REPL...\n"
            )
        )
        self.set_stdin("exec READ 1\nexec WRITE 1\n")
        self.input.appendleft(3)
        self.reset_stdout()
        self.repl.cmdloop()
        self.assertEqual(
            self.stdout.getvalue(),
            (
                f"{self.repl.prompt * 2}Output: 3\n"
                f"{self.repl.prompt}Exiting REPL...\n"
            )
        )
        self.assertEqual(self.repl.machine.counter, 3)

    def test_reset(self) -> None:
        """Test the reset command"""
        self.set_stdin("exec LIT 3\nreset\n")
        self.repl.cmdloop()
        self.assertEqual(
            self.stdout.getvalue(),
            f"{self.repl.prompt * 3}Exiting REPL...\n"
        )
        self.assertEqual(self.repl.machine.counter, 1)

    def test_status(self) -> None:
        """Test the status command"""
        self.set_stdin("exec LIT 3\nstatus\n")
        self.repl.cmdloop()
        status = "".join(f"{key}: {value}\n" for key, value in self.repl.machine.status().items())
        self.assertEqual(
            self.stdout.getvalue(),
            f"{self.repl.prompt * 2}{status}{self.repl.prompt}Exiting REPL...\n"
        )

    def test_state(self) -> None:
        """Test the state command"""
        self.set_stdin("exec LIT 3\nexec LIT 42\nexec EQ\nstate\n")
        self.repl.cmdloop()
        self.assertEqual(
            self.stdout.getvalue(),
            (
                f"{self.repl.prompt * 4}(4, 0, [], ε, ε)\n"
                f"{self.repl.prompt}Exiting REPL...\n"
            )
        )
