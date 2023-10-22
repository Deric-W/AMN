#!/usr/bin/python3

"""AM0 Tests"""

from unittest import TestCase
from AMN.am0 import Machine, Instruction


# do not remove trailing whitespace!
EXAMPLE_PROGRAM1 = \
"""
READ 2;  
LIT 1;
STORE 1;
LIT 0;

STORE 3;
LOAD 1;
LOAD 2;
LE;   
JMC 21;
LOAD 3;
LOAD 1;
LOAD 1;
MUL;   
ADD;
   
STORE 3;
LOAD 1;
LIT 1;
ADD;
STORE 1;
JMP 6;
WRITE 3;
"""

EXAMPLE_PROGRAM2 = \
"""
READ 1;
LOAD 1;
LIT 7;
LIT 1;
SUB;
DIV;
LIT 2;
MOD;
STORE 1;
LOAD 1;
LIT 0;
EQ;
LOAD 1;
LIT 0;
NE;
LOAD 1;
LIT 0;
LT;
LOAD 1;
LIT 0;
GT;
LOAD 1;
LIT 1;
LE;
LOAD 1;
LIT 1;
GE;
WRITE 1;
STORE 2;
WRITE 2;
STORE 2;
WRITE 2;
STORE 2;
WRITE 2;
STORE 2;
WRITE 2;
STORE 2;
WRITE 2;
STORE 2;
WRITE 2;
"""


class InstructionTest(TestCase):
    """AM0 instruction tests"""

    def test_parse(self) -> None:
        """test instruction parsing"""
        self.assertEqual(
            Instruction.parse("ADD"),
            (Instruction.ADD, 0)
        )
        self.assertEqual(
            Instruction.parse("JMP 42"),
            (Instruction.JMP, 42)
        )
        with self.assertRaises(ValueError):
            Instruction.parse("JMP x")
        with self.assertRaises(KeyError):
            Instruction.parse("XXX")

    def test_parse_program(self) -> None:
        """test program parsing"""
        self.assertEqual(
            list(Instruction.parse_program(EXAMPLE_PROGRAM1)),
            [
                (Instruction.READ, 2),
                (Instruction.LIT, 1),
                (Instruction.STORE, 1),
                (Instruction.LIT, 0),
                (Instruction.STORE, 3),
                (Instruction.LOAD, 1),
                (Instruction.LOAD, 2),
                (Instruction.LE, 0),
                (Instruction.JMC, 21),
                (Instruction.LOAD, 3),
                (Instruction.LOAD, 1),
                (Instruction.LOAD, 1),
                (Instruction.MUL, 0),
                (Instruction.ADD, 0),
                (Instruction.STORE, 3),
                (Instruction.LOAD, 1),
                (Instruction.LIT, 1),
                (Instruction.ADD, 0),
                (Instruction.STORE, 1),
                (Instruction.JMP, 6),
                (Instruction.WRITE, 3)
            ]
        )
        self.assertEqual(list(Instruction.parse_program("")), [])
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1;\nADD\nJMP 3;"))
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1; XXX; ADD;"))
        with self.assertRaises(ValueError):
            list(Instruction.parse_program("LOAD 1;\n ADD;\nJMP 3;"))

    def test_has_payload(self) -> None:
        """test payload information"""
        has_payload = {
            Instruction.LIT,
            Instruction.LOAD,
            Instruction.STORE,
            Instruction.JMP,
            Instruction.JMC,
            Instruction.READ,
            Instruction.WRITE
        }
        for instruction in Instruction:
            self.assertEqual(
                instruction.has_payload(),
                instruction in has_payload,
                f"invalid payload data for {instruction}"
            )

    def test_is_jump(self) -> None:
        """test jump information"""
        is_jump = {
            Instruction.JMP,
            Instruction.JMC
        }
        for instruction in Instruction:
            self.assertEqual(
                instruction.is_jump(),
                instruction in is_jump,
                f"invalid jump data for {instruction}"
            )


class MachineTest(TestCase):
    """AM0 machine tests"""

    def test_default(self) -> None:
        """test default state"""
        machine = Machine.default(iter([]))
        self.assertEqual(machine.counter, 1)
        self.assertEqual(machine.stack, [])
        self.assertEqual(machine.memory, {})

    def test_reset(self) -> None:
        """test reset state"""
        iterator = iter(range(0))
        machine = Machine(42, [1, 2], {3: 4, 5: 6}, iterator)
        machine.reset()
        self.assertEqual(machine.counter, 1)
        self.assertEqual(machine.stack, [])
        self.assertEqual(machine.memory, {})
        self.assertIs(machine.input, iterator)

    def test_status(self) -> None:
        """test status information"""
        machines = [
            Machine.default(iter([])),
            Machine(42, [1, 2], {3: 4, 5: 6}, iter(range(9)))
        ]
        for machine in machines:
            status = machine.status()
            self.assertIn("Counter", status)
            self.assertIn("Stack", status)
            self.assertIn("Memory", status)

    def test_state(self) -> None:
        """test state representation"""
        self.assertEqual(
            Machine.default(iter(range(3))).state([], []),
            "(1, ε, [], ε, ε)"
        )
        self.assertEqual(
            Machine(42, [1, 2], {3: 4, 5: 6}, iter(range(9))).state(range(1, 3), range(2)),
            "(42, 2 : 1, [3/4, 5/6], 1 : 2, 0 : 1)"
        )

    def test_execute(self) -> None:
        """test program execution"""
        program1 = tuple(Instruction.parse_program(EXAMPLE_PROGRAM1))
        program2 = tuple(Instruction.parse_program(EXAMPLE_PROGRAM2))
        machine = Machine.default(iter([2, 42]))
        self.assertEqual(
            list(machine.execute_program(program1)),
            [None] * 39 + [5]
        )
        self.assertEqual(
            list(filter(lambda value: value is not None, machine.execute_program(program2))),
            [1, 1, 1, 1, 0, 1, 0]
        )
        self.assertIsNone(next(machine.input, None))
